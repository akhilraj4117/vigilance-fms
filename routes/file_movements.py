"""
File Movements routes for the Flask application.
This matches the desktop app's File Movements Tab functionality.
"""
import json
import random
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, Response
from flask_login import login_required, current_user
from models import (File, PREntry, TraceDetails, ReportSoughtDetails, ReportAskedDetails,
                    CMOPortalDetails, RTIApplication, FileMigration, Communication,
                    InquiryDetails, DisciplinaryAction, Institution, PreliminaryStatement,
                    Rule15Statement, FileType, Category)
from extensions import db, csrf
from utils import convert_date_format
from sqlalchemy import or_, and_, func
import csv
from io import StringIO
from datetime import datetime, timedelta

file_movements_bp = Blueprint('file_movements', __name__)


def get_file_types():
    """Get all file types from database."""
    try:
        return [ft.name for ft in FileType.query.order_by(FileType.name).all()]
    except:
        # Return defaults if table doesn't exist yet
        return [
            "Women Harassment", "Police Case", "Medical Negligence",
            "Attack on Doctors", "Attack on Staffs", "Unauthorised Absence",
            "RTI", "Duty Lapse", "Private Practice", "Denial of Treatment",
            "Social Security Pension", "Others"
        ]


def get_categories():
    """Get all categories from database."""
    try:
        return [c.name for c in Category.query.order_by(Category.name).all()]
    except:
        # Return defaults if table doesn't exist yet
        return [
            "CMO Portal", "RVU", "KeSCPCR", "KHRC", "NKS",
            "SC/ST", "KWC", "Court Case", "Rajya/Lok/Niyamasabha",
            "Vig & Anti Corruption", "Complaint", "Others"
        ]


# Constants
FILE_STATUSES = [
    "With Clerk", "Submitted", "Despatched", "Closed", "Mailed & Despatched",
    "Parked", "Stock File", "Attached", "Speak", "Handed Over"
]


# =============================================================================
# Main File Movements Page
# =============================================================================
@file_movements_bp.route('/')
@login_required
def index():
    """File Movements main page with sub-tab navigation."""
    return render_template('file_movements/index.html')


# =============================================================================
# Search Files Sub-Tab
# =============================================================================
@file_movements_bp.route('/search')
@login_required
def search_files():
    """Search Files sub-tab - comprehensive file search with filters."""
    page = request.args.get('page', 1, type=int)
    per_page = 25
    
    # Get filter parameters
    general_search = request.args.get('q', '').strip()
    file_type = request.args.get('file_type', '')
    category = request.args.get('category', '')
    status = request.args.get('status', '')
    file_status = request.args.get('file_status', 'all')  # active/closed/all
    institution = request.args.get('institution', '')
    from_year = request.args.get('from_year', '')
    to_year = request.args.get('to_year', '')
    
    # Build query
    query = File.query
    
    # General search across multiple fields
    if general_search:
        query = query.filter(
            or_(
                File.file_number.ilike(f'%{general_search}%'),
                File.subject.ilike(f'%{general_search}%'),
                File.details_of_file.ilike(f'%{general_search}%'),
                File.institution_name.ilike(f'%{general_search}%')
            )
        )
    
    # Filter by file type
    if file_type:
        query = query.filter(File.type_of_file.ilike(f'%{file_type}%'))
    
    # Filter by category
    if category:
        query = query.filter(File.category.ilike(f'%{category}%'))
    
    # Filter by status
    if status:
        query = query.filter(File.status == status)
    
    # Filter by active/closed
    if file_status == 'active':
        query = query.filter(or_(File.is_closed == 0, File.is_closed == None))
    elif file_status == 'closed':
        query = query.filter(File.is_closed == 1)
    
    # Filter by institution
    if institution:
        query = query.filter(File.institution_name.ilike(f'%{institution}%'))
    
    # Filter by year range
    if from_year:
        query = query.filter(File.file_year >= from_year)
    if to_year:
        query = query.filter(File.file_year <= to_year)
    
    # Order by file number
    query = query.order_by(File.file_number.desc())
    
    # Paginate
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    files = pagination.items
    
    # Get institutions for dropdown
    institutions = Institution.query.order_by(Institution.name.asc()).all()
    
    return render_template('file_movements/search_files.html',
                          files=files,
                          pagination=pagination,
                          general_search=general_search,
                          file_type=file_type,
                          category=category,
                          status=status,
                          file_status=file_status,
                          institution=institution,
                          from_year=from_year,
                          to_year=to_year,
                          file_types=get_file_types(),
                          categories=get_categories(),
                          statuses=FILE_STATUSES,
                          institutions=institutions)


@file_movements_bp.route('/search/export')
@login_required
def export_search_results():
    """Export search results to CSV."""
    # Get filter parameters (same as search_files)
    general_search = request.args.get('q', '').strip()
    file_type = request.args.get('file_type', '')
    status = request.args.get('status', '')
    file_status = request.args.get('file_status', 'all')
    institution = request.args.get('institution', '')
    
    query = File.query
    
    if general_search:
        query = query.filter(
            or_(
                File.file_number.ilike(f'%{general_search}%'),
                File.subject.ilike(f'%{general_search}%'),
                File.details_of_file.ilike(f'%{general_search}%')
            )
        )
    
    if file_type:
        query = query.filter(File.type_of_file.ilike(f'%{file_type}%'))
    if status:
        query = query.filter(File.status == status)
    if file_status == 'active':
        query = query.filter(or_(File.is_closed == 0, File.is_closed == None))
    elif file_status == 'closed':
        query = query.filter(File.is_closed == 1)
    if institution:
        query = query.filter(File.institution_name.ilike(f'%{institution}%'))
    
    files = query.all()
    
    output = StringIO()
    # Add UTF-8 BOM for Excel to recognize Unicode characters (Malayalam etc.)
    output.write('\ufeff')
    writer = csv.writer(output)
    writer.writerow(['File Number', 'Subject', 'Details', 'Status', 'Type', 'Category', 'Institution', 'Is Closed'])
    
    for f in files:
        writer.writerow([
            f.file_number,
            f.subject or '',
            f.details_of_file or '',
            f.status or '',
            f.type_of_file or '',
            f.category or '',
            f.institution_name or '',
            'Yes' if f.is_closed else 'No'
        ])
    
    output.seek(0)
    return Response(
        output.getvalue().encode('utf-8-sig'),
        mimetype='text/csv; charset=utf-8-sig',
        headers={'Content-Disposition': f'attachment; filename=search_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'}
    )


# =============================================================================
# View PR Entries Sub-Tab
# =============================================================================
@file_movements_bp.route('/pr-entries')
@login_required
def pr_entries():
    """View all PR entries grouped by file number."""
    from collections import OrderedDict
    import re
    
    view_mode = request.args.get('view', 'all')  # 'all' or 'current'
    current_file = request.args.get('file', '')
    page = request.args.get('page', 1, type=int)
    per_page = 500  # Increased to show more entries per page for better grouping
    
    def extract_year_and_number(file_number):
        """Extract year and number from file_number like 'DMOH-TVM/1066/2024-A6'"""
        if not file_number:
            return ('9999', 0)
        # Pattern: prefix/number/year-suffix
        match = re.search(r'/(\d+)/(\d{4})', file_number)
        if match:
            num = int(match.group(1))
            year = match.group(2)
            return (year, num)
        return ('9999', 0)
    
    # Handle different view modes
    if view_mode == 'current':
        if current_file:
            # Show only current file's PR entries
            query = PREntry.query.filter(PREntry.file_number == current_file)
            query = query.order_by(PREntry.serial_number.asc())
            pagination = query.paginate(page=page, per_page=per_page, error_out=False)
            pr_entries_list = pagination.items
            
            # Group by file number
            grouped_entries = OrderedDict()
            for entry in pr_entries_list:
                if entry.file_number not in grouped_entries:
                    grouped_entries[entry.file_number] = []
                grouped_entries[entry.file_number].append(entry)
        else:
            # No file loaded - return empty results
            return render_template('file_movements/pr_entries.html',
                                  grouped_entries={},
                                  pagination=None,
                                  view_mode=view_mode,
                                  current_file=current_file,
                                  no_file_loaded=True)
    else:
        # Show all files' PR entries - exclude closed files
        # First get all PR entries with their files
        query = PREntry.query.join(File, PREntry.file_number == File.file_number).filter(
            or_(File.is_closed == 0, File.is_closed == None)
        )
        
        # Get all entries (we'll sort in Python since year is embedded in file_number)
        all_entries = query.all()
        
        # Sort entries by extracted year, then file number, then serial number
        def get_serial_int(sn):
            """Convert serial_number to int safely"""
            if sn is None:
                return 0
            try:
                return int(sn)
            except (ValueError, TypeError):
                return 0
        
        all_entries.sort(key=lambda e: (
            extract_year_and_number(e.file_number)[0],  # year
            extract_year_and_number(e.file_number)[1],  # number within year
            get_serial_int(e.serial_number)
        ))
        
        # Manual pagination
        total = len(all_entries)
        start = (page - 1) * per_page
        end = start + per_page
        pr_entries_list = all_entries[start:end]
        
        # Create a simple pagination object
        class SimplePagination:
            def __init__(self, items, page, per_page, total):
                self.items = items
                self.page = page
                self.per_page = per_page
                self.total = total
                self.pages = (total + per_page - 1) // per_page if per_page > 0 else 1
                self.has_prev = page > 1
                self.has_next = page < self.pages
                self.prev_num = page - 1 if self.has_prev else None
                self.next_num = page + 1 if self.has_next else None
            
            def iter_pages(self, left_edge=2, left_current=2, right_current=3, right_edge=2):
                last = 0
                for num in range(1, self.pages + 1):
                    if num <= left_edge or \
                       (self.page - left_current <= num <= self.page + right_current) or \
                       num > self.pages - right_edge:
                        if last + 1 != num:
                            yield None
                        yield num
                        last = num
        
        pagination = SimplePagination(pr_entries_list, page, per_page, total)
        
        # Group by file number for tree-like display (maintain order using OrderedDict)
        grouped_entries = OrderedDict()
        for entry in pr_entries_list:
            if entry.file_number not in grouped_entries:
                grouped_entries[entry.file_number] = []
            grouped_entries[entry.file_number].append(entry)
        
        return render_template('file_movements/pr_entries.html',
                              grouped_entries=grouped_entries,
                              pagination=pagination,
                              view_mode=view_mode,
                              current_file=current_file,
                              no_file_loaded=False)
    
    return render_template('file_movements/pr_entries.html',
                          grouped_entries=grouped_entries,
                          pagination=pagination,
                          view_mode=view_mode,
                          current_file=current_file,
                          no_file_loaded=False)


@file_movements_bp.route('/pr-entries/export')
@login_required
def export_pr_entries():
    """Export PR entries to Excel/CSV."""
    import re
    
    def extract_year_and_number(file_number):
        """Extract year and number from file_number like 'DMOH-TVM/1066/2024-A6'"""
        if not file_number:
            return ('9999', 0)
        match = re.search(r'/(\d+)/(\d{4})', file_number)
        if match:
            num = int(match.group(1))
            year = match.group(2)
            return (year, num)
        return ('9999', 0)
    
    file_number = request.args.get('file', '')
    
    if file_number:
        # Export specific file's PR entries
        query = PREntry.query.filter(PREntry.file_number == file_number)
        entries = query.order_by(PREntry.serial_number.asc()).all()
    else:
        # Export all files' PR entries - exclude closed files
        query = PREntry.query.join(File, PREntry.file_number == File.file_number).filter(
            or_(File.is_closed == 0, File.is_closed == None)
        )
        entries = query.all()
        
        # Sort by extracted year, then file number, then serial number
        def get_serial_int(sn):
            if sn is None:
                return 0
            try:
                return int(sn)
            except (ValueError, TypeError):
                return 0
        
        entries.sort(key=lambda e: (
            extract_year_and_number(e.file_number)[0],  # year
            extract_year_and_number(e.file_number)[1],  # number within year
            get_serial_int(e.serial_number)
        ))
    
    output = StringIO()
    # Add UTF-8 BOM for Excel to recognize Unicode characters (Malayalam etc.)
    output.write('\ufeff')
    writer = csv.writer(output)
    writer.writerow([
        'File Number', 'Serial Number', 'Current Number', 'Date Receipt Clerk', 'Title',
        'From Whom Outside (Name)', 'From Whom Outside (Number)', 'From Whom Outside (Date)',
        'Submitted by Clerk (Date)', 'Return to Clerk (Date)', 'Reference Issued To',
        'Reference Issued Date', 'Disposal Nature', 'Disposal Date'
    ])
    
    for e in entries:
        writer.writerow([
            e.file_number, e.serial_number, e.current_number, e.date_receipt_clerk,
            e.title, e.from_whom_outside_name, e.from_whom_outside_number,
            e.from_whom_outside_date, e.submitted_by_clerk_date, e.return_to_clerk_date,
            e.reference_issued_to_whom, e.reference_issued_date, e.disposal_nature,
            e.disposal_date
        ])
    
    output.seek(0)
    filename = f'pr_entries_{file_number}_{datetime.now().strftime("%Y%m%d")}.csv' if file_number else f'pr_entries_all_{datetime.now().strftime("%Y%m%d")}.csv'
    return Response(
        output.getvalue().encode('utf-8-sig'),
        mimetype='text/csv; charset=utf-8-sig',
        headers={'Content-Disposition': f'attachment; filename={filename}'}
    )


# =============================================================================
# Physical Files Sub-Tab
# =============================================================================
@file_movements_bp.route('/physical-files')
@login_required
def physical_files():
    """Physical Files sub-tab - files with physical trace details."""
    page = request.args.get('page', 1, type=int)
    per_page = 25
    
    # Get files with physical trace details (almirah, rack, row info)
    query = File.query.filter(
        or_(
            File.almirah != None,
            File.almirah != '',
            File.rack != None,
            File.rack != '',
            File.row != None,
            File.row != ''
        )
    )
    
    # Also include files with trace_details
    # For simplicity, just show all Physical files
    query = File.query.filter(File.file_type == 'Physical')
    
    query = query.order_by(File.file_number.asc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    files = pagination.items
    
    return render_template('file_movements/physical_files.html',
                          files=files,
                          pagination=pagination)


@file_movements_bp.route('/physical-files/export')
@login_required
def export_physical_files():
    """Export physical files to Excel."""
    files = File.query.filter(File.file_type == 'Physical').all()
    
    output = StringIO()
    # Add UTF-8 BOM for Excel to recognize Unicode characters (Malayalam etc.)
    output.write('\ufeff')
    writer = csv.writer(output)
    writer.writerow(['File Number', 'Subject', 'Details', 'Almirah', 'Rack', 'Row', 
                    'Migrated to E-Office', 'E-Office File No.', 'Status'])
    
    for f in files:
        writer.writerow([
            f.file_number, f.subject or '', f.details_of_file or '',
            f.almirah or '', f.rack or '', f.row or '',
            f.migrated_to_eoffice or 'No', f.eoffice_file_number or 'NA',
            'Closed' if f.is_closed else 'Active'
        ])
    
    output.seek(0)
    return Response(
        output.getvalue().encode('utf-8-sig'),
        mimetype='text/csv; charset=utf-8-sig',
        headers={'Content-Disposition': f'attachment; filename=physical_files_{datetime.now().strftime("%Y%m%d")}.csv'}
    )


# =============================================================================
# Pending Files Sub-Tab (with inner tabs)
# =============================================================================
@file_movements_bp.route('/pending')
@login_required
def pending_files():
    """Pending Files main page with sub-tab navigation."""
    tab = request.args.get('tab', 'report_sought')
    return render_template('file_movements/pending_files.html', active_tab=tab)


@file_movements_bp.route('/pending/report-sought')
@login_required
def pending_report_sought():
    """Report Sought - Pending Reports."""
    search = request.args.get('q', '').strip()
    
    # Get pending reports (submitted != 'Yes' and has report_sought_date)
    query = ReportSoughtDetails.query.filter(
        and_(
            or_(ReportSoughtDetails.submitted != 'Yes', ReportSoughtDetails.submitted == None),
            ReportSoughtDetails.report_sought_date != None,
            ReportSoughtDetails.report_sought_date != ''
        )
    )
    
    if search:
        query = query.filter(
            or_(
                ReportSoughtDetails.file_number.ilike(f'%{search}%'),
                ReportSoughtDetails.subject.ilike(f'%{search}%')
            )
        )
    
    reports = query.all()
    
    return render_template('file_movements/pending_report_sought.html',
                          reports=reports,
                          search=search)


@file_movements_bp.route('/pending/report-sought/export')
@login_required
def export_report_sought():
    """Export Report Sought pending reports to Excel."""
    search = request.args.get('q', '').strip()
    
    # Get pending reports (submitted != 'Yes' and has report_sought_date)
    query = ReportSoughtDetails.query.filter(
        and_(
            or_(ReportSoughtDetails.submitted != 'Yes', ReportSoughtDetails.submitted == None),
            ReportSoughtDetails.report_sought_date != None,
            ReportSoughtDetails.report_sought_date != ''
        )
    )
    
    if search:
        query = query.filter(
            or_(
                ReportSoughtDetails.file_number.ilike(f'%{search}%'),
                ReportSoughtDetails.subject.ilike(f'%{search}%')
            )
        )
    
    reports = query.all()
    
    output = StringIO()
    # Add UTF-8 BOM for Excel to recognize Unicode characters
    output.write('\ufeff')
    writer = csv.writer(output)
    writer.writerow([
        'Sl. No.', 'File Number', 'Subject', 'Body', 'Report Sought Date',
        'Status', 'Institution', 'Details'
    ])
    
    for idx, report in enumerate(reports, 1):
        writer.writerow([
            idx,
            report.file_number or '',
            report.subject or '',
            report.body or '',
            report.report_sought_date or '',
            report.status or '',
            report.institution or '',
            report.details or ''
        ])
    
    output.seek(0)
    filename = f'pending_report_sought_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    return Response(
        output.getvalue().encode('utf-8-sig'),
        mimetype='text/csv; charset=utf-8-sig',
        headers={'Content-Disposition': f'attachment; filename={filename}'}
    )


@file_movements_bp.route('/pending/report-asked')
@login_required
def pending_report_asked():
    """Report Asked - Pending Reports."""
    search = request.args.get('q', '').strip()
    
    # Get pending reports with file subject (join with File table)
    query = db.session.query(ReportAskedDetails, File.subject).outerjoin(
        File, ReportAskedDetails.file_number == File.file_number
    ).filter(
        and_(
            or_(ReportAskedDetails.report_submitted != 'Yes', ReportAskedDetails.report_submitted == None),
            ReportAskedDetails.whether_report_asked == 'Yes'
        )
    )
    
    if search:
        query = query.filter(
            or_(
                ReportAskedDetails.file_number.ilike(f'%{search}%'),
                ReportAskedDetails.institution_name.ilike(f'%{search}%'),
                File.subject.ilike(f'%{search}%')
            )
        )
    
    results = query.all()
    
    return render_template('file_movements/pending_report_asked.html',
                          reports=results,
                          search=search)


@file_movements_bp.route('/pending/report-asked/export')
@login_required
def export_report_asked():
    """Export Report Asked pending reports to Excel."""
    search = request.args.get('q', '').strip()
    
    # Get pending reports with file subject (join with File table)
    query = db.session.query(ReportAskedDetails, File.subject).outerjoin(
        File, ReportAskedDetails.file_number == File.file_number
    ).filter(
        and_(
            or_(ReportAskedDetails.report_submitted != 'Yes', ReportAskedDetails.report_submitted == None),
            ReportAskedDetails.whether_report_asked == 'Yes'
        )
    )
    
    if search:
        query = query.filter(
            or_(
                ReportAskedDetails.file_number.ilike(f'%{search}%'),
                ReportAskedDetails.institution_name.ilike(f'%{search}%'),
                File.subject.ilike(f'%{search}%')
            )
        )
    
    results = query.all()
    
    output = StringIO()
    # Add UTF-8 BOM for Excel to recognize Unicode characters
    output.write('\ufeff')
    writer = csv.writer(output)
    writer.writerow([
        'Sl. No.', 'File Number', 'Subject', 'Asked Date', 'Institution Name',
        'Report Submitted', 'Received Date'
    ])
    
    for idx, (report, subject) in enumerate(results, 1):
        writer.writerow([
            idx,
            report.file_number or '',
            subject or '',
            report.asked_date or '',
            report.institution_name or '',
            report.report_submitted or 'No',
            report.received_date or ''
        ])
    
    output.seek(0)
    filename = f'pending_report_asked_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    return Response(
        output.getvalue().encode('utf-8-sig'),
        mimetype='text/csv; charset=utf-8-sig',
        headers={'Content-Disposition': f'attachment; filename={filename}'}
    )


@file_movements_bp.route('/pending/cmo-portal')
@login_required
def pending_cmo_portal():
    """CMO Portal - Pending Files (not finalised)."""
    search = request.args.get('q', '').strip()
    
    query = CMOPortalDetails.query.filter(
        or_(CMOPortalDetails.finalised != 'Yes', CMOPortalDetails.finalised == None)
    )
    
    if search:
        query = query.filter(
            or_(
                CMOPortalDetails.file_number.ilike(f'%{search}%'),
                CMOPortalDetails.docket_number.ilike(f'%{search}%')
            )
        )
    
    files = query.all()
    
    return render_template('file_movements/pending_cmo_portal.html',
                          files=files,
                          search=search)


@file_movements_bp.route('/pending/rti-files')
@login_required
def pending_rti_files():
    """RTI Files - Not Closed."""
    search = request.args.get('q', '').strip()
    
    # Get RTI applications where status is not 'Closed' and file is not closed
    query = db.session.query(RTIApplication, File).outerjoin(
        File, RTIApplication.file_number == File.file_number
    ).filter(
        and_(
            or_(
                func.lower(RTIApplication.status) != 'closed',
                RTIApplication.status == None,
                RTIApplication.status == ''
            ),
            or_(File.is_closed == 0, File.is_closed == None, File == None)
        )
    )
    
    if search:
        query = query.filter(
            or_(
                RTIApplication.file_number.ilike(f'%{search}%'),
                RTIApplication.original_application_no.ilike(f'%{search}%'),
                RTIApplication.applicant_name.ilike(f'%{search}%')
            )
        )
    
    query = query.order_by(RTIApplication.date_of_receipt.desc())
    results = query.all()
    
    return render_template('file_movements/pending_rti_files.html',
                          results=results,
                          search=search)


@file_movements_bp.route('/pending/inquiry-not-submitted')
@login_required
def pending_inquiry_not_submitted():
    """Inquiry - Report not Submitted."""
    inquiry_type = request.args.get('type', 'preliminary')
    
    if inquiry_type == 'preliminary':
        # Preliminary inquiry: conducted but report not submitted
        # Query InquiryDetails joined with DisciplinaryAction to get file info
        query = db.session.query(InquiryDetails, DisciplinaryAction, File).outerjoin(
            DisciplinaryAction, InquiryDetails.file_number == DisciplinaryAction.file_number
        ).outerjoin(
            File, InquiryDetails.file_number == File.file_number
        ).filter(
            and_(
                InquiryDetails.prelim_conducted == 1,
                or_(
                    InquiryDetails.prelim_report_submitted == 0,
                    InquiryDetails.prelim_report_submitted == None
                )
            )
        )
    else:  # rule15
        # Rule 15(ii) inquiry: conducted but report not submitted
        query = db.session.query(InquiryDetails, DisciplinaryAction, File).outerjoin(
            DisciplinaryAction, InquiryDetails.file_number == DisciplinaryAction.file_number
        ).outerjoin(
            File, InquiryDetails.file_number == File.file_number
        ).filter(
            and_(
                InquiryDetails.rule15_conducted == 1,
                or_(
                    InquiryDetails.rule15_report_submitted == 0,
                    InquiryDetails.rule15_report_submitted == None
                )
            )
        )
    
    if inquiry_type == 'preliminary':
        results = query.all()
        return render_template('file_movements/pending_inquiry.html',
                              results=results,
                              inquiry_type=inquiry_type,
                              is_preliminary=True)
    else:
        results = query.all()
        return render_template('file_movements/pending_inquiry.html',
                              results=results,
                              inquiry_type=inquiry_type,
                              is_preliminary=False)


# =============================================================================
# Migrated Files Sub-Tab
# =============================================================================
@file_movements_bp.route('/migrated')
@login_required
def migrated_files():
    """Migrated Files - files migrated to e-office (like desktop app)."""
    page = request.args.get('page', 1, type=int)
    per_page = 25
    
    # Get files from file_migrations table with joined file details
    # Using raw SQL to match desktop app behavior
    from sqlalchemy import text
    
    # Build migrated files list with subject and details from joined files
    migrations_data = []
    migrations_query = FileMigration.query.order_by(FileMigration.migration_date.desc())
    pagination = migrations_query.paginate(page=page, per_page=per_page, error_out=False)
    
    for migration in pagination.items:
        # Get physical file details
        physical_file = File.query.filter_by(file_number=migration.physical_file_number).first()
        # Get eoffice file details
        eoffice_file = File.query.filter_by(file_number=migration.eoffice_file_number).first()
        
        # Use eoffice subject/details first, fallback to physical file
        subject = ''
        details = ''
        if eoffice_file:
            subject = eoffice_file.subject or ''
            details = eoffice_file.details_of_file or ''
        if not subject and physical_file:
            subject = physical_file.subject or ''
        if not details and physical_file:
            details = physical_file.details_of_file or ''
        
        migrations_data.append({
            'physical_file_number': migration.physical_file_number,
            'eoffice_file_number': migration.eoffice_file_number,
            'subject': subject,
            'details': details,
            'migration_date': migration.migration_date
        })
    
    return render_template('file_movements/migrated_files.html',
                          migrations=migrations_data,
                          pagination=pagination)



# =============================================================================
# Communications Sub-Tab
# =============================================================================
@file_movements_bp.route('/communications')
@login_required
def communications():
    """Communications - Malayalam document management with split-pane layout like desktop app."""
    page = request.args.get('page', 1, type=int)
    per_page = 25
    file_number = request.args.get('file', '').strip()
    selected_id = request.args.get('selected', None, type=int)
    
    if file_number:
        # File-specific view (split-pane layout like desktop app)
        communications_list = Communication.query.filter(
            Communication.file_number == file_number
        ).order_by(Communication.modified_date.desc()).all()
        
        # Get selected communication content if any
        selected_content = None
        if selected_id:
            selected_comm = Communication.query.get(selected_id)
            if selected_comm:
                selected_content = selected_comm.content
        
        return render_template('file_movements/communications.html',
                              communications=communications_list,
                              pagination=None,
                              file_number=file_number,
                              selected_id=selected_id,
                              selected_content=selected_content)
    else:
        # All communications view (table format)
        query = Communication.query.order_by(Communication.modified_date.desc())
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        communications_list = pagination.items
        
        return render_template('file_movements/communications.html',
                              communications=communications_list,
                              pagination=pagination,
                              file_number='',
                              selected_id=None,
                              selected_content=None)


@file_movements_bp.route('/communications/list')
@login_required
def list_communications():
    """List communications for a specific file via AJAX."""
    file_number = request.args.get('file', '').strip()
    if not file_number:
        return jsonify({'success': False, 'communications': []})
    
    comms = Communication.query.filter_by(file_number=file_number).order_by(
        Communication.modified_date.desc()
    ).all()
    
    def get_comm_name(c):
        """Get communication name from available fields."""
        # Skip 'Untitled Communication' and prefer document_title
        if c.communication_name and c.communication_name.strip() and c.communication_name.strip() != 'Untitled Communication':
            return c.communication_name.strip()
        if c.document_title and c.document_title.strip():
            return c.document_title.strip()
        if c.document_type and c.document_type.strip():
            return c.document_type.strip()
        return 'Untitled'
    
    return jsonify({
        'success': True,
        'communications': [{
            'id': c.id,
            'name': get_comm_name(c),
            'created_date': c.created_date,
            'modified_date': c.modified_date
        } for c in comms]
    })


@file_movements_bp.route('/communications/debug')
@login_required
def debug_communications():
    """Debug endpoint to see raw communication data."""
    file_number = request.args.get('file', '').strip()
    if not file_number:
        return jsonify({'error': 'No file number provided. Use ?file=YOUR_FILE_NUMBER'})
    
    comms = Communication.query.filter_by(file_number=file_number).all()
    return jsonify({
        'count': len(comms),
        'file_number': file_number,
        'communications': [{
            'id': c.id,
            'communication_name': repr(c.communication_name),
            'document_title': repr(c.document_title),
            'document_type': repr(c.document_type),
            'content_length': len(c.content) if c.content else 0,
            'malayalam_content_length': len(c.malayalam_content) if c.malayalam_content else 0
        } for c in comms]
    })


@file_movements_bp.route('/communications/content/<int:id>')
@login_required
def get_communication_content(id):
    """Get communication content via AJAX."""
    comm = Communication.query.get_or_404(id)
    # Get the best available name (skip 'Untitled Communication')
    name = 'Untitled'
    if comm.communication_name and comm.communication_name.strip() and comm.communication_name.strip() != 'Untitled Communication':
        name = comm.communication_name.strip()
    elif comm.document_title and comm.document_title.strip():
        name = comm.document_title.strip()
    elif comm.document_type and comm.document_type.strip():
        name = comm.document_type.strip()
    
    return jsonify({
        'success': True,
        'content': comm.content or '',
        'name': name
    })


@file_movements_bp.route('/communications/add', methods=['POST'])
@csrf.exempt
@login_required
def add_communication():
    """Add a new communication."""
    try:
        data = request.get_json(force=True, silent=True)
        if not data:
            return jsonify({'success': False, 'message': 'No data received or invalid JSON.'}), 200
        
        file_number = data.get('file_number', '').strip()
        name = data.get('name', '').strip()
        
        if not file_number or not name:
            return jsonify({'success': False, 'message': 'File number and name are required.'}), 200
        
        # Check if file exists (due to foreign key constraint)
        from models import File
        file_exists = File.query.filter_by(file_number=file_number).first()
        if not file_exists:
            return jsonify({'success': False, 'message': f'File "{file_number}" does not exist in the database.'}), 200
        
        # Check for duplicate
        existing = Communication.query.filter_by(file_number=file_number, communication_name=name).first()
        if existing:
            return jsonify({'success': False, 'message': 'A communication with this name already exists for this file.'}), 200
        
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        comm = Communication(
            file_number=file_number,
            communication_name=name,
            document_type='Letter',
            document_title=name,
            malayalam_content='',
            content='',
            created_date=now,
            modified_date=now,
            created_by=current_user.username if current_user.is_authenticated else 'User'
        )
        
        db.session.add(comm)
        db.session.commit()
        return jsonify({'success': True, 'id': comm.id}), 200
    except Exception as e:
        db.session.rollback()
        import traceback
        return jsonify({'success': False, 'message': f'Server error: {str(e)}'}), 200



@file_movements_bp.route('/communications/update-name', methods=['POST'])
@csrf.exempt
@login_required
def update_communication_name():
    """Update communication name."""
    data = request.get_json()
    comm_id = data.get('id')
    name = data.get('name', '').strip()
    
    if not comm_id or not name:
        return jsonify({'success': False, 'message': 'ID and name are required.'})
    
    comm = Communication.query.get_or_404(comm_id)
    
    # Check for duplicate (excluding current)
    existing = Communication.query.filter(
        Communication.file_number == comm.file_number,
        Communication.communication_name == name,
        Communication.id != comm_id
    ).first()
    if existing:
        return jsonify({'success': False, 'message': 'A communication with this name already exists for this file.'})
    
    try:
        comm.communication_name = name
        comm.modified_date = datetime.now().isoformat()
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})


@file_movements_bp.route('/communications/delete', methods=['POST'])
@csrf.exempt
@login_required
def delete_communication():
    """Delete a communication."""
    data = request.get_json()
    comm_id = data.get('id')
    
    if not comm_id:
        return jsonify({'success': False, 'message': 'ID is required.'})
    
    comm = Communication.query.get_or_404(comm_id)
    
    try:
        db.session.delete(comm)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})


@file_movements_bp.route('/communications/save', methods=['POST'])
@csrf.exempt
@login_required
def save_communication_content():
    """Save communication content."""
    data = request.get_json()
    comm_id = data.get('id')
    content = data.get('content', '')
    
    if not comm_id:
        return jsonify({'success': False, 'message': 'ID is required.'})
    
    comm = Communication.query.get_or_404(comm_id)
    
    try:
        comm.content = content
        comm.modified_date = datetime.now().isoformat()
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})


@file_movements_bp.route('/communications/export/<int:id>')
@login_required
def export_communication(id):
    """Export communication to Word document (.doc format using HTML that Word can open)."""
    comm = Communication.query.get_or_404(id)
    
    # Create HTML document that Microsoft Word can open directly as .doc
    # This uses the MIME type and HTML structure that Word recognizes
    html_content = f"""<!DOCTYPE html>
<html xmlns:o="urn:schemas-microsoft-com:office:office"
      xmlns:w="urn:schemas-microsoft-com:office:word"
      xmlns="http://www.w3.org/TR/REC-html40">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
    <!--[if gte mso 9]>
    <xml>
        <w:WordDocument>
            <w:View>Print</w:View>
            <w:Zoom>100</w:Zoom>
            <w:DoNotOptimizeForBrowser/>
        </w:WordDocument>
    </xml>
    <![endif]-->
    <title>{comm.communication_name}</title>
    <style>
        @page {{ size: A4; margin: 1in; }}
        body {{ 
            font-family: 'Mangal', 'Nirmala UI', 'Arial Unicode MS', Arial, sans-serif; 
            font-size: 12pt;
            line-height: 1.5;
            padding: 0;
            margin: 0;
        }}
        h1 {{ font-size: 16pt; margin-bottom: 10pt; }}
        p {{ margin: 6pt 0; }}
        table {{ border-collapse: collapse; width: 100%; }}
        td, th {{ border: 1px solid #000; padding: 5pt; }}
    </style>
</head>
<body>
    <div style="margin-bottom: 20pt;">
        <h1>{comm.communication_name}</h1>
        <p><strong>File Number:</strong> {comm.file_number}</p>
        <p><strong>Created Date:</strong> {comm.created_date}</p>
    </div>
    <hr style="border: 1px solid #000; margin: 10pt 0;">
    <div>
        {comm.content or ''}
    </div>
</body>
</html>"""
    
    # Safe filename
    safe_filename = "".join(c for c in comm.communication_name if c.isalnum() or c in (' ', '-', '_')).strip()
    safe_filename = safe_filename.replace(' ', '_') if safe_filename else 'communication'
    
    return Response(
        html_content,
        mimetype='application/msword',
        headers={
            'Content-Disposition': f'attachment; filename="{safe_filename}.doc"',
            'Content-Type': 'application/msword'
        }
    )


@file_movements_bp.route('/communications/view/<int:id>')
@login_required
def view_communication(id):
    """View a communication document."""
    comm = Communication.query.get_or_404(id)
    return render_template('file_movements/view_communication.html', communication=comm)


# =============================================================================
# Speak Files Sub-Tab
# =============================================================================
@file_movements_bp.route('/speak')
@login_required
def speak_files():
    """Speak Files - files with 'Speak' status (like desktop app)."""
    search = request.args.get('q', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = 25
    
    # Filter files with 'Speak' status
    query = File.query.filter(File.status == 'Speak')
    
    # Search filter (like desktop app - searches all visible columns)
    if search:
        query = query.filter(
            or_(
                File.file_number.ilike(f'%{search}%'),
                File.subject.ilike(f'%{search}%'),
                File.details_of_file.ilike(f'%{search}%'),
                File.type_of_file.ilike(f'%{search}%'),
                File.category.ilike(f'%{search}%'),
                File.institution_name.ilike(f'%{search}%')
            )
        )
    
    query = query.order_by(File.follow_up_date.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    files = pagination.items
    total = pagination.total
    total_pages = pagination.pages
    
    return render_template('file_movements/speak_files.html',
                          files=files,
                          pagination=pagination,
                          page=page,
                          per_page=per_page,
                          total=total,
                          total_pages=total_pages,
                          today=datetime.now().date(),
                          search=search)


@file_movements_bp.route('/speak/export')
@login_required
def export_speak_files():
    """Export Speak files to CSV."""
    files = File.query.filter(File.status == 'Speak').all()
    
    output = StringIO()
    # Add UTF-8 BOM for Excel to recognize Unicode characters (Malayalam etc.)
    output.write('\ufeff')
    writer = csv.writer(output)
    writer.writerow(['File Number', 'Subject', 'Details', 'File Type', 'Category', 
                    'Institution', 'Follow-up Date'])
    
    for f in files:
        writer.writerow([
            f.file_number, f.subject or '', f.details_of_file or '',
            f.type_of_file or '', f.category or '', 
            f.institution_name or '', f.follow_up_date or ''
        ])
    
    output.seek(0)
    return Response(
        output.getvalue().encode('utf-8-sig'),
        mimetype='text/csv; charset=utf-8-sig',
        headers={'Content-Disposition': f'attachment; filename=speak_files_{datetime.now().strftime("%Y%m%d")}.csv'}
    )


# =============================================================================
# API Endpoints
# =============================================================================
@file_movements_bp.route('/api/file/<file_number>')
@login_required
def api_get_file(file_number):
    """Get file details as JSON."""
    file = File.query.filter_by(file_number=file_number).first()
    if not file:
        return jsonify({'error': 'File not found'}), 404
    
    return jsonify({
        'file_number': file.file_number,
        'subject': file.subject,
        'details': file.details_of_file,
        'status': file.status,
        'institution': file.institution_name,
        'is_closed': file.is_closed
    })


# =============================================================================
# Follow-up Files Sub-Tab (matching desktop app)
# =============================================================================
def parse_date(date_str):
    """Parse date string in DD-MM-YYYY format to datetime.date object."""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, '%d-%m-%Y').date()
    except:
        try:
            return datetime.strptime(date_str, '%Y-%m-%d').date()
        except:
            return None


def get_files_by_followup_status(status_type):
    """Get files based on follow-up status - matching desktop app logic."""
    today = datetime.now().date()
    files = []
    
    # Get all non-closed files with follow-up dates (excluding Handed Over files)
    query = File.query.filter(
        and_(
            or_(File.is_closed == 0, File.is_closed == None),
            or_(File.status != 'Handed Over', File.status == None),
            File.follow_up_date != None,
            File.follow_up_date != ''
        )
    )
    
    all_files = query.all()
    
    for f in all_files:
        follow_up_date = parse_date(f.follow_up_date)
        if not follow_up_date:
            continue
        
        days_diff = (follow_up_date - today).days
        
        if status_type == 'today':
            if days_diff == 0:
                files.append(f)
        elif status_type == '5days':
            if 1 <= days_diff <= 5:
                files.append(f)
        elif status_type == '10days':
            if 6 <= days_diff <= 10:
                files.append(f)
        elif status_type == 'exceeded':
            if days_diff < 0:
                files.append(f)
        elif status_type == 'completed':
            # Completed follow-up - files that were marked as completed (closed)
            pass  # Handle separately
    
    return files


@file_movements_bp.route('/follow-up')
@login_required
def follow_up_files():
    """Follow-up Files tab - matching desktop app."""
    tab = request.args.get('tab', 'today')
    
    today = datetime.now().date()
    
    # Get files for each category
    today_files = get_files_by_followup_status('today')
    five_days_files = get_files_by_followup_status('5days')
    ten_days_files = get_files_by_followup_status('10days')
    exceeded_files = get_files_by_followup_status('exceeded')
    
    # Completed follow-up: closed files
    completed_files = File.query.filter(
        and_(
            File.is_closed == 1,
            File.follow_up_date != None,
            File.follow_up_date != ''
        )
    ).order_by(File.closed_date.desc()).limit(100).all()
    
    # Select the active tab's files
    if tab == 'today':
        files = today_files
    elif tab == '5days':
        files = five_days_files
    elif tab == '10days':
        files = ten_days_files
    elif tab == 'exceeded':
        files = exceeded_files
    elif tab == 'completed':
        files = completed_files
    else:
        files = today_files
    
    return render_template('file_movements/follow_up_files.html',
                          files=files,
                          tab=tab,
                          today_count=len(today_files),
                          five_days_count=len(five_days_files),
                          ten_days_count=len(ten_days_files),
                          exceeded_count=len(exceeded_files),
                          completed_count=len(completed_files),
                          today=today)


@file_movements_bp.route('/follow-up/mark-completed', methods=['POST'])
@login_required
def mark_follow_up_completed():
    """Mark a follow-up as completed."""
    file_number = request.form.get('file_number')
    next_follow_up_date = request.form.get('next_follow_up_date')
    no_further_follow_up = request.form.get('no_further_follow_up') == 'on'
    remarks = request.form.get('remarks', '')
    
    file = File.query.filter_by(file_number=file_number).first()
    if not file:
        flash('File not found.', 'danger')
        return redirect(url_for('file_movements.follow_up_files'))
    
    if no_further_follow_up:
        # Clear follow-up date but don't close the file
        file.follow_up_date = None
        if remarks:
            existing_remarks = file.remarks or ''
            file.remarks = f"{existing_remarks}\n[{datetime.now().strftime('%d-%m-%Y')}] Follow-up completed: {remarks}".strip()
    elif next_follow_up_date:
        # Set new follow-up date
        file.follow_up_date = convert_date_format(next_follow_up_date)
        if remarks:
            existing_remarks = file.remarks or ''
            file.remarks = f"{existing_remarks}\n[{datetime.now().strftime('%d-%m-%Y')}] {remarks}".strip()
    
    file.last_modified = datetime.now().isoformat()
    db.session.commit()
    
    flash('Follow-up updated successfully.', 'success')
    return redirect(url_for('file_movements.follow_up_files'))


@file_movements_bp.route('/follow-up/randomize', methods=['POST'])
@login_required
def randomize_exceeded_dates():
    """Randomize follow-up dates for Date Exceeded files in batches of 10."""
    exceeded_files = get_files_by_followup_status('exceeded')
    
    if not exceeded_files:
        flash('No files found in Date Exceeded tab.', 'warning')
        return redirect(url_for('file_movements.follow_up_files', tab='exceeded'))
    
    base_date = datetime.now().date() + timedelta(days=1)
    updated_count = 0
    
    for idx, f in enumerate(exceeded_files):
        batch_number = idx // 10
        new_date = base_date + timedelta(days=batch_number)
        f.follow_up_date = new_date.strftime('%d-%m-%Y')
        f.last_modified = datetime.now().isoformat()
        updated_count += 1
    
    db.session.commit()
    
    flash(f'Successfully updated {updated_count} file(s). Files distributed starting from {base_date.strftime("%d-%m-%Y")}.', 'success')
    return redirect(url_for('file_movements.follow_up_files', tab='exceeded'))


@file_movements_bp.route('/follow-up/randomize-all', methods=['POST'])
@login_required
def randomize_all_files():
    """Randomize follow-up dates for ALL active files with max 25 per day."""
    # Get all non-closed files (excluding Handed Over files)
    active_files = File.query.filter(
        and_(
            or_(File.is_closed == 0, File.is_closed == None),
            or_(File.status != 'Handed Over', File.status == None)
        )
    ).all()
    
    if not active_files:
        flash('No active files found.', 'warning')
        return redirect(url_for('file_movements.follow_up_files', tab='exceeded'))
    
    # Shuffle files randomly
    random.shuffle(active_files)
    
    base_date = datetime.now().date() + timedelta(days=1)
    files_per_day = 25
    updated_count = 0
    
    for idx, f in enumerate(active_files):
        day_number = idx // files_per_day
        new_date = base_date + timedelta(days=day_number)
        f.follow_up_date = new_date.strftime('%d-%m-%Y')
        f.last_modified = datetime.now().isoformat()
        updated_count += 1
    
    db.session.commit()
    
    days_needed = (len(active_files) + files_per_day - 1) // files_per_day
    flash(f'Successfully randomized {updated_count} file(s) across {days_needed} day(s) starting from {base_date.strftime("%d-%m-%Y")}.', 'success')
    return redirect(url_for('file_movements.follow_up_files', tab='exceeded'))


@file_movements_bp.route('/follow-up/export')
@login_required
def export_follow_up_files():
    """Export follow-up files to CSV."""
    tab = request.args.get('tab', 'today')
    
    if tab == 'completed':
        files = File.query.filter(
            and_(
                File.is_closed == 1,
                File.follow_up_date != None
            )
        ).all()
    else:
        files = get_files_by_followup_status(tab)
    
    output = StringIO()
    # Add UTF-8 BOM for Excel to recognize Unicode characters (Malayalam etc.)
    output.write('\ufeff')
    writer = csv.writer(output)
    writer.writerow(['File Number', 'Subject', 'Details', 'Follow-up Date', 'Status', 'Institution'])
    
    for f in files:
        writer.writerow([
            f.file_number,
            f.subject or '',
            f.details_of_file or '',
            f.follow_up_date or '',
            f.status or '',
            f.institution_name or ''
        ])
    
    output.seek(0)
    return Response(
        output.getvalue().encode('utf-8-sig'),
        mimetype='text/csv; charset=utf-8-sig',
        headers={'Content-Disposition': f'attachment; filename=follow_up_{tab}_{datetime.now().strftime("%Y%m%d")}.csv'}
    )
