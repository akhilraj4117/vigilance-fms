"""
Disciplinary action routes for the Flask application.
"""
import json
import csv
import io
from datetime import datetime, timedelta
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, Response
from flask_login import login_required, current_user
from models import DisciplinaryAction, UnauthorisedAbsentee, File, Employee, InquiryDetails, CourtCase, SocialSecurityPension, RemarksEntry, Institution
from extensions import db
from sqlalchemy import or_, text

disciplinary_bp = Blueprint('disciplinary', __name__)


def get_superannuation_counts():
    """Helper function to get superannuation counts for all sub-tabs."""
    sql = text("""
        SELECT d.date_superannuation, e.date_of_birth
        FROM disciplinary_action_details d
        LEFT JOIN employees e ON d.pen = e.pen
        WHERE d.pen IS NOT NULL AND d.pen != ''
        AND (d.finalised_date IS NULL OR d.finalised_date = '')
    """)
    
    da_records = db.session.execute(sql).fetchall()
    
    today = datetime.now()
    one_year_future = today + timedelta(days=365)
    two_years_future = today + timedelta(days=730)
    
    counts = {
        'within_1_year': 0,
        'within_2_years': 0,
        'retired': 0,
        'total': 0
    }
    
    for record in da_records:
        da_super_date, emp_dob = record
        
        super_date = None
        if da_super_date and str(da_super_date).strip():
            for fmt in ['%d-%m-%Y', '%Y-%m-%d', '%d/%m/%Y']:
                try:
                    super_date = datetime.strptime(str(da_super_date).strip(), fmt)
                    break
                except:
                    continue
        
        if not super_date and emp_dob and str(emp_dob).strip():
            try:
                dob = datetime.strptime(str(emp_dob).strip(), '%d-%m-%Y')
                super_date = dob.replace(year=dob.year + 60)
            except:
                pass
        
        if super_date:
            if today <= super_date <= one_year_future:
                counts['within_1_year'] += 1
                counts['total'] += 1
            elif one_year_future < super_date <= two_years_future:
                counts['within_2_years'] += 1
                counts['total'] += 1
            elif super_date < today:
                counts['retired'] += 1
                counts['total'] += 1
    
    return counts


def get_pending_counts():
    """Helper function to get pending notices counts for all sub-tabs."""
    # Get migrated and closed files to exclude
    migrated_sql = text("""
        SELECT file_number FROM files WHERE file_type = 'Physical' OR file_type = 'Physical File'
    """)
    closed_sql = text("""
        SELECT file_number FROM files WHERE is_closed = 1
    """)
    
    try:
        migrated_files = {str(row[0]).strip() for row in db.session.execute(migrated_sql).fetchall() if row[0]}
    except:
        migrated_files = set()
    
    try:
        closed_files = {str(row[0]).strip() for row in db.session.execute(closed_sql).fetchall() if row[0]}
    except:
        closed_files = set()
    
    # Get all disciplinary action details
    da_sql = text("""
        SELECT file_number, action_taking_office, moc_issued, moc_receipt_date, wsd_received_date,
               probation_termination_notice, scn_issued_date, scn_receipt_date, scn_reply_date
        FROM disciplinary_action_details
        WHERE (finalised_date IS NULL OR finalised_date = '')
    """)
    
    da_records = db.session.execute(da_sql).fetchall()
    
    counts = {
        'moc_dmo': 0, 'moc_dhs': 0,
        'ptn_dmo': 0, 'ptn_dhs': 0,
        'scn_dmo': 0, 'scn_dhs': 0,
        'wsd_pending': 0, 'scn_reply': 0,
        'total': 0
    }
    
    for record in da_records:
        (file_number, action_taking_office, moc_issued, moc_receipt_date, wsd_received_date,
         ptn, scn_issued_date, scn_receipt_date, scn_reply_date) = record
        
        file_num_str = str(file_number).strip() if file_number else ''
        if file_num_str in migrated_files or file_num_str in closed_files:
            continue
        
        action_office = str(action_taking_office).strip().upper() if action_taking_office else ''
        moc_issued_val = str(moc_issued).strip().lower() if moc_issued else ''
        moc_receipt_str = str(moc_receipt_date).strip() if moc_receipt_date else ''
        wsd_received_str = str(wsd_received_date).strip() if wsd_received_date else ''
        ptn_val = str(ptn).strip().lower() if ptn else ''
        scn_issued_str = str(scn_issued_date).strip() if scn_issued_date else ''
        scn_receipt_str = str(scn_receipt_date).strip() if scn_receipt_date else ''
        scn_reply_str = str(scn_reply_date).strip() if scn_reply_date else ''
        
        if moc_issued_val == 'issued' and action_office == 'DMO' and not moc_receipt_str:
            counts['moc_dmo'] += 1
        if moc_issued_val == 'issued' and (action_office == 'DHS' or action_office == 'DHS/GOVT') and not moc_receipt_str:
            counts['moc_dhs'] += 1
        if ptn_val == 'issued' and action_office == 'DMO' and not scn_receipt_str:
            counts['ptn_dmo'] += 1
        if ptn_val == 'issued' and (action_office == 'DHS' or action_office == 'DHS/GOVT') and not scn_receipt_str:
            counts['ptn_dhs'] += 1
        if scn_issued_str and action_office == 'DMO' and not scn_receipt_str:
            counts['scn_dmo'] += 1
        if scn_issued_str and (action_office == 'DHS' or action_office == 'DHS/GOVT') and not scn_receipt_str:
            counts['scn_dhs'] += 1
        if moc_issued_val == 'issued' and moc_receipt_str and not wsd_received_str:
            counts['wsd_pending'] += 1
        if scn_issued_str and scn_receipt_str and not scn_reply_str:
            counts['scn_reply'] += 1
    
    counts['total'] = sum([counts[k] for k in counts if k != 'total'])
    
    return counts


@disciplinary_bp.route('/dashboard')
@login_required
def index():
    """Main disciplinary dashboard with sub-tabs (matching desktop app)."""
    tab = request.args.get('tab', 'ua_details')
    inner_tab = request.args.get('inner_tab', 'ua')
    page = request.args.get('page', 1, type=int)
    per_page = 20
    search_query = request.args.get('q', '').strip()
    sort_by = request.args.get('sort', '')
    sort_order = request.args.get('order', 'asc')
    
    # Additional filter parameters for all columns
    institution_filter = request.args.get('institution', '').strip()
    designation_filter = request.args.get('designation', '').strip()
    willingness_filter = request.args.get('willingness', '').strip()
    present_status_filter = request.args.get('present_status', '').strip()
    probation_status_filter = request.args.get('probation_status', '').strip()
    group_by_designation = request.args.get('group_by_designation', '')
    moc_filter = request.args.get('moc', '').strip()
    major_minor_filter = request.args.get('major_minor', '').strip()
    refunded_filter = request.args.get('refunded', '').strip()
    finalised_filter = request.args.get('finalised', '').strip()
    prelim_filter = request.args.get('prelim_conducted', '').strip()
    rule15_filter = request.args.get('rule15_conducted', '').strip()
    court_forum_filter = request.args.get('court_forum', '').strip()
    court_status_filter = request.args.get('court_status', '').strip()
    
    results = []
    pagination = None
    designation_stats = {}  # For designation statistics modal
    
    # Get unique values for filter dropdowns
    institutions = db.session.query(DisciplinaryAction.institution).distinct().filter(
        DisciplinaryAction.institution != None, DisciplinaryAction.institution != ''
    ).order_by(DisciplinaryAction.institution.asc()).all()
    institutions = [i[0] for i in institutions]
    
    designations = db.session.query(DisciplinaryAction.designation).distinct().filter(
        DisciplinaryAction.designation != None, DisciplinaryAction.designation != ''
    ).order_by(DisciplinaryAction.designation.asc()).all()
    designations = [d[0] for d in designations]
    
    # Get unique present_status values for UA filter
    present_statuses = db.session.query(UnauthorisedAbsentee.present_status).distinct().filter(
        UnauthorisedAbsentee.present_status != None, UnauthorisedAbsentee.present_status != ''
    ).order_by(UnauthorisedAbsentee.present_status.asc()).all()
    present_statuses = [p[0] for p in present_statuses]
    
    # Get unique court forums for Court Case filter
    court_forums = db.session.query(CourtCase.name_of_forum).distinct().filter(
        CourtCase.name_of_forum != None, CourtCase.name_of_forum != ''
    ).order_by(CourtCase.name_of_forum.asc()).all()
    court_forums = [c[0] for c in court_forums]
    
    if tab == 'ua_details':
        # UA Details tab with inner tabs
        query = db.session.query(DisciplinaryAction, UnauthorisedAbsentee).join(
            UnauthorisedAbsentee, DisciplinaryAction.id == UnauthorisedAbsentee.da_id
        )
        
        # Apply inner tab filters (matching desktop app logic)
        if inner_tab == 'ua':
            # Main UA tab excludes: Rejoined, Retired, and Finalised records
            # This matches desktop app filter in load_unauthorised_absentees()
            query = query.filter(
                or_(
                    UnauthorisedAbsentee.present_status.is_(None),
                    UnauthorisedAbsentee.present_status == '',
                    ~UnauthorisedAbsentee.present_status.in_(['Rejoined', 'Retired'])
                )
            ).filter(
                or_(
                    DisciplinaryAction.finalised_date.is_(None),
                    DisciplinaryAction.finalised_date == ''
                )
            )
        elif inner_tab == 'rejoined':
            query = query.filter(UnauthorisedAbsentee.present_status == 'Rejoined')
        elif inner_tab == 'finalised_ua':
            query = query.filter(
                DisciplinaryAction.finalised_date.isnot(None),
                DisciplinaryAction.finalised_date != ''
            )
        elif inner_tab == 'retired':
            query = query.filter(UnauthorisedAbsentee.present_status == 'Retired')
        # ua_all - no filter
        
        # Search filter
        if search_query:
            query = query.filter(
                or_(
                    DisciplinaryAction.pen.ilike(f'%{search_query}%'),
                    DisciplinaryAction.employee_name.ilike(f'%{search_query}%'),
                    DisciplinaryAction.institution.ilike(f'%{search_query}%'),
                    DisciplinaryAction.file_number.ilike(f'%{search_query}%')
                )
            )
        
        # Additional filters for UA tab
        if institution_filter:
            query = query.filter(DisciplinaryAction.institution == institution_filter)
        if designation_filter:
            query = query.filter(DisciplinaryAction.designation == designation_filter)
        if willingness_filter:
            query = query.filter(UnauthorisedAbsentee.willingness == willingness_filter)
        if present_status_filter:
            query = query.filter(UnauthorisedAbsentee.present_status == present_status_filter)
        
        # Probation status filter (matching desktop app)
        if probation_status_filter:
            if probation_status_filter == 'Declared':
                query = query.filter(
                    DisciplinaryAction.probation.isnot(None),
                    DisciplinaryAction.probation != '',
                    DisciplinaryAction.probation.ilike('%declared%')
                )
            elif probation_status_filter == 'Not Declared':
                query = query.filter(
                    or_(
                        DisciplinaryAction.probation.is_(None),
                        DisciplinaryAction.probation == '',
                        ~DisciplinaryAction.probation.ilike('%declared%')
                    )
                )
        
        # Calculate designation statistics before pagination (for modal)
        stats_query = db.session.query(
            DisciplinaryAction.designation, 
            db.func.count(DisciplinaryAction.id)
        ).join(
            UnauthorisedAbsentee, DisciplinaryAction.id == UnauthorisedAbsentee.da_id
        )
        
        # Apply same inner_tab filter for stats
        if inner_tab == 'ua':
            stats_query = stats_query.filter(
                or_(
                    UnauthorisedAbsentee.present_status.is_(None),
                    UnauthorisedAbsentee.present_status == '',
                    ~UnauthorisedAbsentee.present_status.in_(['Rejoined', 'Retired'])
                )
            ).filter(
                or_(
                    DisciplinaryAction.finalised_date.is_(None),
                    DisciplinaryAction.finalised_date == ''
                )
            )
        elif inner_tab == 'rejoined':
            stats_query = stats_query.filter(UnauthorisedAbsentee.present_status == 'Rejoined')
        elif inner_tab == 'finalised_ua':
            stats_query = stats_query.filter(
                DisciplinaryAction.finalised_date.isnot(None),
                DisciplinaryAction.finalised_date != ''
            )
        elif inner_tab == 'retired':
            stats_query = stats_query.filter(UnauthorisedAbsentee.present_status == 'Retired')
        
        stats_query = stats_query.group_by(DisciplinaryAction.designation)
        designation_stats = {row[0] or 'Not Specified': row[1] for row in stats_query.all()}
        
        # Apply sorting for UA tab
        if group_by_designation:
            # Group by Designation - sort by designation first, then by employee name
            query = query.order_by(DisciplinaryAction.designation.asc(), DisciplinaryAction.employee_name.asc())
        elif sort_by:
            sort_column = None
            if sort_by == 'employee_name':
                sort_column = DisciplinaryAction.employee_name
            elif sort_by == 'pen':
                sort_column = DisciplinaryAction.pen
            elif sort_by == 'designation':
                sort_column = DisciplinaryAction.designation
            elif sort_by == 'institution':
                sort_column = DisciplinaryAction.institution
            elif sort_by == 'date_from_ua':
                sort_column = UnauthorisedAbsentee.date_from_ua
            elif sort_by == 'present_status':
                sort_column = UnauthorisedAbsentee.present_status
            elif sort_by == 'willingness':
                sort_column = UnauthorisedAbsentee.willingness
            elif sort_by == 'file_number':
                sort_column = DisciplinaryAction.file_number
            
            if sort_column is not None:
                if sort_order == 'desc':
                    query = query.order_by(sort_column.desc())
                else:
                    query = query.order_by(sort_column.asc())
            else:
                query = query.order_by(DisciplinaryAction.id.desc())
        else:
            query = query.order_by(DisciplinaryAction.id.desc())
        
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        results = pagination.items
        
    elif tab == 'disciplinary':
        # Disciplinary Action tab with inner tabs
        query = DisciplinaryAction.query
        
        # Apply inner tab filters
        if inner_tab == 'proceedings':
            # DA not finalised
            query = query.filter(
                or_(
                    DisciplinaryAction.finalised_date.is_(None),
                    DisciplinaryAction.finalised_date == ''
                )
            )
        elif inner_tab == 'finalised_da':
            # DA finalised
            query = query.filter(
                DisciplinaryAction.finalised_date.isnot(None),
                DisciplinaryAction.finalised_date != ''
            )
        elif inner_tab == 'pending':
            # Pending notices - MOC issued but not finalised
            query = query.filter(
                DisciplinaryAction.moc_issued == 'Yes',
                or_(
                    DisciplinaryAction.finalised_date.is_(None),
                    DisciplinaryAction.finalised_date == ''
                )
            )
        
        # Search filter
        if search_query:
            query = query.filter(
                or_(
                    DisciplinaryAction.pen.ilike(f'%{search_query}%'),
                    DisciplinaryAction.employee_name.ilike(f'%{search_query}%'),
                    DisciplinaryAction.institution.ilike(f'%{search_query}%'),
                    DisciplinaryAction.file_number.ilike(f'%{search_query}%')
                )
            )
        
        # Additional filters for DA tab
        if institution_filter:
            query = query.filter(DisciplinaryAction.institution == institution_filter)
        if designation_filter:
            query = query.filter(DisciplinaryAction.designation == designation_filter)
        if moc_filter:
            query = query.filter(DisciplinaryAction.moc_issued == moc_filter)
        if major_minor_filter:
            query = query.filter(DisciplinaryAction.major_minor == major_minor_filter)
        if finalised_filter:
            if finalised_filter == 'Yes':
                query = query.filter(
                    DisciplinaryAction.finalised_date.isnot(None),
                    DisciplinaryAction.finalised_date != ''
                )
            elif finalised_filter == 'No':
                query = query.filter(
                    or_(
                        DisciplinaryAction.finalised_date.is_(None),
                        DisciplinaryAction.finalised_date == ''
                    )
                )
        
        # Apply sorting for DA tab
        if sort_by:
            sort_column = None
            if sort_by == 'employee_name':
                sort_column = DisciplinaryAction.employee_name
            elif sort_by == 'pen':
                sort_column = DisciplinaryAction.pen
            elif sort_by == 'designation':
                sort_column = DisciplinaryAction.designation
            elif sort_by == 'institution':
                sort_column = DisciplinaryAction.institution
            elif sort_by == 'file_number':
                sort_column = DisciplinaryAction.file_number
            elif sort_by == 'moc_issued':
                sort_column = DisciplinaryAction.moc_issued
            elif sort_by == 'major_minor':
                sort_column = DisciplinaryAction.major_minor
            elif sort_by == 'finalised_date':
                sort_column = DisciplinaryAction.finalised_date
            
            if sort_column is not None:
                if sort_order == 'desc':
                    query = query.order_by(sort_column.desc())
                else:
                    query = query.order_by(sort_column.asc())
            else:
                query = query.order_by(DisciplinaryAction.id.desc())
        else:
            query = query.order_by(DisciplinaryAction.id.desc())
        
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        results = pagination.items
        
    elif tab == 'inquiry':
        # Inquiry Details tab - matches desktop app with two separate tables
        # Get filter for "Report Not Submitted"
        report_not_submitted_filter = request.args.get('report_not_submitted', '')
        
        # Query for Preliminary Inquiry records (with File join for subject/details)
        prelim_query = db.session.query(File, InquiryDetails).join(
            InquiryDetails, File.file_number == InquiryDetails.file_number
        ).filter(InquiryDetails.prelim_conducted == 1)
        
        # Query for Rule 15(ii) Inquiry records
        rule15_query = db.session.query(File, InquiryDetails).join(
            InquiryDetails, File.file_number == InquiryDetails.file_number
        ).filter(InquiryDetails.rule15_conducted == 1)
        
        if search_query:
            search_filter = or_(
                File.file_number.ilike(f'%{search_query}%'),
                File.subject.ilike(f'%{search_query}%'),
                InquiryDetails.prelim_io_name.ilike(f'%{search_query}%'),
                InquiryDetails.rule15_io_name.ilike(f'%{search_query}%')
            )
            prelim_query = prelim_query.filter(search_filter)
            rule15_query = rule15_query.filter(search_filter)
        
        # Apply "Report Not Submitted" filter if checked
        if report_not_submitted_filter == 'yes':
            prelim_query = prelim_query.filter(
                or_(InquiryDetails.prelim_report_submitted == 0, 
                    InquiryDetails.prelim_report_submitted.is_(None))
            )
            rule15_query = rule15_query.filter(
                or_(InquiryDetails.rule15_report_submitted == 0, 
                    InquiryDetails.rule15_report_submitted.is_(None))
            )
        
        # Get all results (no pagination for two-table layout like desktop)
        prelim_results = prelim_query.order_by(File.file_number).all()
        rule15_results = rule15_query.order_by(File.file_number).all()
        
        # Create a simple pagination object for template compatibility
        class SimplePagination:
            def __init__(self, total):
                self.total = total
                self.page = 1
                self.pages = 1
                self.has_prev = False
                self.has_next = False
        
        pagination = SimplePagination(len(prelim_results) + len(rule15_results))
        results = {
            'prelim': prelim_results,
            'rule15': rule15_results,
            'report_not_submitted_filter': report_not_submitted_filter
        }
        
    elif tab == 'court_case':
        # Court Case tab - query CourtCase joined with File table
        # This shows all court cases, not just those linked to disciplinary actions
        query = db.session.query(File, CourtCase).join(
            CourtCase, File.file_number == CourtCase.file_number
        )
        
        if search_query:
            query = query.filter(
                or_(
                    File.file_number.ilike(f'%{search_query}%'),
                    File.subject.ilike(f'%{search_query}%'),
                    CourtCase.case_no.ilike(f'%{search_query}%'),
                    CourtCase.name_of_forum.ilike(f'%{search_query}%')
                )
            )
        
        # Additional filters for court case tab
        if court_forum_filter:
            query = query.filter(CourtCase.name_of_forum == court_forum_filter)
        if court_status_filter:
            query = query.filter(CourtCase.present_status.ilike(f'%{court_status_filter}%'))
        
        # Apply sorting for court case tab
        if sort_by:
            sort_column = None
            if sort_by == 'file_number':
                sort_column = File.file_number
            elif sort_by == 'case_no':
                sort_column = CourtCase.case_no
            elif sort_by == 'court_name':
                sort_column = CourtCase.name_of_forum
            
            if sort_column is not None:
                if sort_order == 'desc':
                    query = query.order_by(sort_column.desc())
                else:
                    query = query.order_by(sort_column.asc())
            else:
                query = query.order_by(CourtCase.id.desc())
        else:
            query = query.order_by(CourtCase.id.desc())
        
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        results = pagination.items
        
    elif tab == 'ssp':
        # Social Security Pension tab - query SSP table directly
        query = SocialSecurityPension.query
        
        if search_query:
            query = query.filter(
                or_(
                    SocialSecurityPension.pen.ilike(f'%{search_query}%'),
                    SocialSecurityPension.name.ilike(f'%{search_query}%'),
                    SocialSecurityPension.file_number.ilike(f'%{search_query}%')
                )
            )
        
        # Additional filters for SSP tab
        if refunded_filter:
            query = query.filter(SocialSecurityPension.refunded_status == refunded_filter)
        if finalised_filter:
            query = query.filter(SocialSecurityPension.finalised == finalised_filter)
        
        # Apply sorting for SSP tab
        if sort_by:
            sort_column = None
            if sort_by == 'name':
                sort_column = SocialSecurityPension.name
            elif sort_by == 'pen':
                sort_column = SocialSecurityPension.pen
            elif sort_by == 'file_number':
                sort_column = SocialSecurityPension.file_number
            elif sort_by == 'amount':
                sort_column = SocialSecurityPension.amount
            elif sort_by == 'refunded_status':
                sort_column = SocialSecurityPension.refunded_status
            elif sort_by == 'finalised':
                sort_column = SocialSecurityPension.finalised
            
            if sort_column is not None:
                if sort_order == 'desc':
                    query = query.order_by(sort_column.desc())
                else:
                    query = query.order_by(sort_column.asc())
            else:
                query = query.order_by(SocialSecurityPension.id.desc())
        else:
            query = query.order_by(SocialSecurityPension.id.desc())
        
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        results = pagination.items
    
    elif tab == 'superannuation':
        # Superannuation tab - calculate superannuation dates and filter by periods
        # This matches the desktop app's SuperannuationTab with 3 sub-tabs
        
        # Get all non-finalized DA records with employee data using raw SQL (matching desktop app)
        sql = text("""
            SELECT d.id as da_id, d.pen, d.file_number, d.employee_name, d.designation, d.institution,
                   d.date_superannuation, e.date_of_birth, e.name, e.designation AS emp_designation,
                   e.institution_name AS emp_institution
            FROM disciplinary_action_details d
            LEFT JOIN employees e ON d.pen = e.pen
            WHERE d.pen IS NOT NULL AND d.pen != ''
            AND (d.finalised_date IS NULL OR d.finalised_date = '')
        """)
        
        da_records = db.session.execute(sql).fetchall()
        
        today = datetime.now()
        one_year_future = today + timedelta(days=365)
        two_years_future = today + timedelta(days=730)
        
        superannuation_results = []
        
        for record in da_records:
            da_id, pen, file_number, da_name, da_designation, da_institution, da_super_date, emp_dob, emp_name, emp_designation, emp_institution = record
            
            # Determine superannuation date: Priority 1 - DA date, Priority 2 - Calculate from DOB + 60 years
            superannuation_date = None
            if da_super_date and str(da_super_date).strip():
                for fmt in ['%d-%m-%Y', '%Y-%m-%d', '%d/%m/%Y']:
                    try:
                        superannuation_date = datetime.strptime(str(da_super_date).strip(), fmt)
                        break
                    except:
                        continue
            
            if not superannuation_date and emp_dob and str(emp_dob).strip():
                try:
                    dob = datetime.strptime(str(emp_dob).strip(), '%d-%m-%Y')
                    superannuation_date = dob.replace(year=dob.year + 60)
                except:
                    pass
            
            if not superannuation_date:
                continue
            
            # Filter based on inner_tab
            include_record = False
            days_value = 0
            
            if inner_tab == 'within_1_year':
                # Employees retiring within 1 year: today <= superannuation_date <= one_year_future
                if today <= superannuation_date <= one_year_future:
                    include_record = True
                    days_value = (superannuation_date - today).days
            elif inner_tab == 'within_2_years':
                # Employees retiring within 2 years: one_year_future < superannuation_date <= two_years_future
                if one_year_future < superannuation_date <= two_years_future:
                    include_record = True
                    days_value = (superannuation_date - today).days
            elif inner_tab == 'retired':
                # Employees already retired: superannuation_date < today
                if superannuation_date < today:
                    include_record = True
                    days_value = (today - superannuation_date).days
            
            if include_record:
                # Apply search filter
                if search_query:
                    search_lower = search_query.lower()
                    name_match = (emp_name or da_name or '').lower()
                    inst_match = (emp_institution or da_institution or '').lower()
                    pen_match = str(pen).lower() if pen else ''
                    file_match = str(file_number).lower() if file_number else ''
                    
                    if not (search_lower in name_match or search_lower in inst_match or 
                            search_lower in pen_match or search_lower in file_match):
                        continue
                
                superannuation_results.append({
                    'da_id': da_id,
                    'pen': pen,
                    'file_number': file_number or '',
                    'name': emp_name or da_name or '',
                    'designation': emp_designation or da_designation or '',
                    'institution': emp_institution or da_institution or '',
                    'date_of_birth': str(emp_dob) if emp_dob else '',
                    'superannuation_date': superannuation_date.strftime('%d-%m-%Y'),
                    'superannuation_datetime': superannuation_date,
                    'days_remaining': days_value if inner_tab != 'retired' else 0,
                    'days_since': days_value if inner_tab == 'retired' else 0
                })
        
        # Sort by superannuation date
        if inner_tab == 'retired':
            superannuation_results.sort(key=lambda x: x['superannuation_datetime'], reverse=True)
        else:
            superannuation_results.sort(key=lambda x: x['superannuation_datetime'])
        
        # Calculate counts for all sub-tabs
        superannuation_counts = {
            'within_1_year': 0,
            'within_2_years': 0,
            'retired': 0,
            'total': 0
        }
        
        for record in da_records:
            _, _, _, _, _, _, da_super_date, emp_dob, _, _, _ = record
            
            super_date = None
            if da_super_date and str(da_super_date).strip():
                for fmt in ['%d-%m-%Y', '%Y-%m-%d', '%d/%m/%Y']:
                    try:
                        super_date = datetime.strptime(str(da_super_date).strip(), fmt)
                        break
                    except:
                        continue
            
            if not super_date and emp_dob and str(emp_dob).strip():
                try:
                    dob = datetime.strptime(str(emp_dob).strip(), '%d-%m-%Y')
                    super_date = dob.replace(year=dob.year + 60)
                except:
                    pass
            
            if super_date:
                if today <= super_date <= one_year_future:
                    superannuation_counts['within_1_year'] += 1
                    superannuation_counts['total'] += 1
                elif one_year_future < super_date <= two_years_future:
                    superannuation_counts['within_2_years'] += 1
                    superannuation_counts['total'] += 1
                elif super_date < today:
                    superannuation_counts['retired'] += 1
                    superannuation_counts['total'] += 1
        
        # Manual pagination for list results
        total = len(superannuation_results)
        start = (page - 1) * per_page
        end = start + per_page
        results = superannuation_results[start:end]
        
        # Create a simple pagination object
        class SimplePagination:
            def __init__(self, page, per_page, total, items):
                self.page = page
                self.per_page = per_page
                self.total = total
                self.items = items
                self.pages = (total + per_page - 1) // per_page if per_page > 0 else 1
                self.has_prev = page > 1
                self.has_next = page < self.pages
                self.prev_num = page - 1
                self.next_num = page + 1
            
            def iter_pages(self, left_edge=2, left_current=2, right_current=5, right_edge=2):
                last = 0
                for num in range(1, self.pages + 1):
                    if num <= left_edge or \
                       (num > self.page - left_current - 1 and num < self.page + right_current) or \
                       num > self.pages - right_edge:
                        if last + 1 != num:
                            yield None
                        yield num
                        last = num
        
        pagination = SimplePagination(page, per_page, total, results)
        
        return render_template('disciplinary/index.html',
                              tab=tab,
                              inner_tab=inner_tab,
                              results=results,
                              pagination=pagination,
                              superannuation_counts=superannuation_counts,
                              search_query=search_query,
                              sort_by=sort_by,
                              sort_order=sort_order,
                              # Filter values
                              institution_filter=institution_filter,
                              designation_filter=designation_filter,
                              willingness_filter=willingness_filter,
                              present_status_filter=present_status_filter,
                              moc_filter=moc_filter,
                              major_minor_filter=major_minor_filter,
                              refunded_filter=refunded_filter,
                              finalised_filter=finalised_filter,
                              prelim_filter=prelim_filter,
                              rule15_filter=rule15_filter,
                              court_forum_filter=court_forum_filter,
                              court_status_filter=court_status_filter,
                              # Filter options
                              institutions=institutions,
                              designations=designations,
                              present_statuses=present_statuses,
                              court_forums=court_forums)
    
    elif tab == 'pending_notices':
        # Pending Notices tab - matching desktop app's PendingNoticesTab structure
        # Sub-tabs: moc_dmo, moc_dhs, ptn_dmo, ptn_dhs, scn_dmo, scn_dhs, wsd_pending, scn_reply
        
        # Get migrated and closed files to exclude
        migrated_sql = text("""
            SELECT file_number FROM files WHERE file_type = 'Physical' OR file_type = 'Physical File'
        """)
        closed_sql = text("""
            SELECT file_number FROM files WHERE is_closed = 1
        """)
        
        try:
            migrated_files = {str(row[0]).strip() for row in db.session.execute(migrated_sql).fetchall() if row[0]}
        except:
            migrated_files = set()
        
        try:
            closed_files = {str(row[0]).strip() for row in db.session.execute(closed_sql).fetchall() if row[0]}
        except:
            closed_files = set()
        
        # Get all disciplinary action details
        da_sql = text("""
            SELECT id, file_number, pen, employee_name, designation, institution,
                   action_taking_office, moc_issued, moc_date, moc_receipt_date, wsd_received_date,
                   probation_termination_notice, scn_issued_date, scn_receipt_date, scn_reply_date
            FROM disciplinary_action_details
            WHERE (finalised_date IS NULL OR finalised_date = '')
        """)
        
        da_records = db.session.execute(da_sql).fetchall()
        
        pending_results = []
        today = datetime.now()
        
        for record in da_records:
            (da_id, file_number, pen, employee_name, designation, institution,
             action_taking_office, moc_issued, moc_date, moc_receipt_date, wsd_received_date,
             ptn, scn_issued_date, scn_receipt_date, scn_reply_date) = record
            
            # Skip migrated and closed files
            file_num_str = str(file_number).strip() if file_number else ''
            if file_num_str in migrated_files or file_num_str in closed_files:
                continue
            
            include_record = False
            issued_date = None
            due_date = None
            
            # Normalize values
            action_office = str(action_taking_office).strip().upper() if action_taking_office else ''
            moc_issued_val = str(moc_issued).strip().lower() if moc_issued else ''
            moc_date_str = str(moc_date).strip() if moc_date else ''
            moc_receipt_str = str(moc_receipt_date).strip() if moc_receipt_date else ''
            wsd_received_str = str(wsd_received_date).strip() if wsd_received_date else ''
            ptn_val = str(ptn).strip().lower() if ptn else ''
            scn_issued_str = str(scn_issued_date).strip() if scn_issued_date else ''
            scn_receipt_str = str(scn_receipt_date).strip() if scn_receipt_date else ''
            scn_reply_str = str(scn_reply_date).strip() if scn_reply_date else ''
            
            # Check based on inner_tab
            if inner_tab == 'moc_dmo':
                # MOC From DMO: moc_issued='Issued', action_taking_office='DMO', moc_receipt_date is empty
                if moc_issued_val == 'issued' and action_office == 'DMO' and not moc_receipt_str:
                    include_record = True
                    issued_date = moc_date_str
                    
            elif inner_tab == 'moc_dhs':
                # MOC From DHS: moc_issued='Issued', action_taking_office='DHS', moc_receipt_date is empty
                if moc_issued_val == 'issued' and (action_office == 'DHS' or action_office == 'DHS/GOVT') and not moc_receipt_str:
                    include_record = True
                    issued_date = moc_date_str
                    
            elif inner_tab == 'ptn_dmo':
                # PTN From DMO: probation_termination_notice='Issued', action_taking_office='DMO', scn_receipt_date is empty
                if ptn_val == 'issued' and action_office == 'DMO' and not scn_receipt_str:
                    include_record = True
                    issued_date = scn_issued_str  # PTN issued date is stored in scn_issued_date
                    
            elif inner_tab == 'ptn_dhs':
                # PTN From DHS: probation_termination_notice='Issued', action_taking_office='DHS', scn_receipt_date is empty
                if ptn_val == 'issued' and (action_office == 'DHS' or action_office == 'DHS/GOVT') and not scn_receipt_str:
                    include_record = True
                    issued_date = scn_issued_str
                    
            elif inner_tab == 'scn_dmo':
                # SCN From DMO: scn_issued_date exists, action_taking_office='DMO', scn_receipt_date is empty
                if scn_issued_str and action_office == 'DMO' and not scn_receipt_str:
                    include_record = True
                    issued_date = scn_issued_str
                    
            elif inner_tab == 'scn_dhs':
                # SCN From DHS: scn_issued_date exists, action_taking_office='DHS', scn_receipt_date is empty
                if scn_issued_str and (action_office == 'DHS' or action_office == 'DHS/GOVT') and not scn_receipt_str:
                    include_record = True
                    issued_date = scn_issued_str
                    
            elif inner_tab == 'wsd_pending':
                # WSD Pending: moc_issued='Issued', moc_receipt_date exists, wsd_received_date is empty
                if moc_issued_val == 'issued' and moc_receipt_str and not wsd_received_str:
                    include_record = True
                    issued_date = moc_receipt_str
                    
            elif inner_tab == 'scn_reply':
                # SCN Reply Pending: scn_issued_date exists, scn_receipt_date exists, scn_reply_date is empty
                if scn_issued_str and scn_receipt_str and not scn_reply_str:
                    include_record = True
                    issued_date = scn_receipt_str
            
            if include_record:
                # Calculate due date (15 days from issued date)
                due_date_obj = None
                is_overdue = False
                days_overdue = 0
                days_remaining = 0
                
                if issued_date:
                    for fmt in ['%d-%m-%Y', '%Y-%m-%d', '%d/%m/%Y']:
                        try:
                            issued_date_obj = datetime.strptime(issued_date, fmt)
                            due_date_obj = issued_date_obj + timedelta(days=15)
                            break
                        except:
                            continue
                
                if due_date_obj:
                    due_date = due_date_obj.strftime('%d-%m-%Y')
                    if today > due_date_obj:
                        is_overdue = True
                        days_overdue = (today - due_date_obj).days
                    else:
                        days_remaining = (due_date_obj - today).days
                
                # Apply search filter
                if search_query:
                    search_lower = search_query.lower()
                    name_match = (employee_name or '').lower()
                    inst_match = (institution or '').lower()
                    pen_match = str(pen).lower() if pen else ''
                    file_match = str(file_number).lower() if file_number else ''
                    
                    if not (search_lower in name_match or search_lower in inst_match or 
                            search_lower in pen_match or search_lower in file_match):
                        continue
                
                pending_results.append({
                    'da_id': da_id,
                    'file_number': file_number or '',
                    'pen': pen or '',
                    'employee_name': employee_name or '',
                    'designation': designation or '',
                    'institution': institution or '',
                    'issued_date': issued_date or '',
                    'due_date': due_date or '',
                    'is_overdue': is_overdue,
                    'days_overdue': days_overdue,
                    'days_remaining': days_remaining
                })
        
        # Sort by due date (overdue items first)
        pending_results.sort(key=lambda x: (not x['is_overdue'], -x['days_overdue'] if x['is_overdue'] else x['days_remaining']))
        
        # Calculate counts for all sub-tabs
        pending_counts = {
            'moc_dmo': 0, 'moc_dhs': 0,
            'ptn_dmo': 0, 'ptn_dhs': 0,
            'scn_dmo': 0, 'scn_dhs': 0,
            'wsd_pending': 0, 'scn_reply': 0,
            'total': 0
        }
        
        for record in da_records:
            (_, file_number, _, _, _, _,
             action_taking_office, moc_issued, moc_date, moc_receipt_date, wsd_received_date,
             ptn, scn_issued_date, scn_receipt_date, scn_reply_date) = record
            
            file_num_str = str(file_number).strip() if file_number else ''
            if file_num_str in migrated_files or file_num_str in closed_files:
                continue
            
            action_office = str(action_taking_office).strip().upper() if action_taking_office else ''
            moc_issued_val = str(moc_issued).strip().lower() if moc_issued else ''
            moc_receipt_str = str(moc_receipt_date).strip() if moc_receipt_date else ''
            wsd_received_str = str(wsd_received_date).strip() if wsd_received_date else ''
            ptn_val = str(ptn).strip().lower() if ptn else ''
            scn_issued_str = str(scn_issued_date).strip() if scn_issued_date else ''
            scn_receipt_str = str(scn_receipt_date).strip() if scn_receipt_date else ''
            scn_reply_str = str(scn_reply_date).strip() if scn_reply_date else ''
            
            if moc_issued_val == 'issued' and action_office == 'DMO' and not moc_receipt_str:
                pending_counts['moc_dmo'] += 1
            if moc_issued_val == 'issued' and (action_office == 'DHS' or action_office == 'DHS/GOVT') and not moc_receipt_str:
                pending_counts['moc_dhs'] += 1
            if ptn_val == 'issued' and action_office == 'DMO' and not scn_receipt_str:
                pending_counts['ptn_dmo'] += 1
            if ptn_val == 'issued' and (action_office == 'DHS' or action_office == 'DHS/GOVT') and not scn_receipt_str:
                pending_counts['ptn_dhs'] += 1
            if scn_issued_str and action_office == 'DMO' and not scn_receipt_str:
                pending_counts['scn_dmo'] += 1
            if scn_issued_str and (action_office == 'DHS' or action_office == 'DHS/GOVT') and not scn_receipt_str:
                pending_counts['scn_dhs'] += 1
            if moc_issued_val == 'issued' and moc_receipt_str and not wsd_received_str:
                pending_counts['wsd_pending'] += 1
            if scn_issued_str and scn_receipt_str and not scn_reply_str:
                pending_counts['scn_reply'] += 1
        
        pending_counts['total'] = sum([pending_counts[k] for k in pending_counts if k != 'total'])
        
        # Manual pagination
        total = len(pending_results)
        start = (page - 1) * per_page
        end = start + per_page
        results = pending_results[start:end]
        
        class SimplePagination:
            def __init__(self, page, per_page, total, items):
                self.page = page
                self.per_page = per_page
                self.total = total
                self.items = items
                self.pages = (total + per_page - 1) // per_page if per_page > 0 else 1
                self.has_prev = page > 1
                self.has_next = page < self.pages
                self.prev_num = page - 1
                self.next_num = page + 1
            
            def iter_pages(self, left_edge=2, left_current=2, right_current=5, right_edge=2):
                last = 0
                for num in range(1, self.pages + 1):
                    if num <= left_edge or \
                       (num > self.page - left_current - 1 and num < self.page + right_current) or \
                       num > self.pages - right_edge:
                        if last + 1 != num:
                            yield None
                        yield num
                        last = num
        
        pagination = SimplePagination(page, per_page, total, results)
        
        return render_template('disciplinary/index.html',
                              tab=tab,
                              inner_tab=inner_tab,
                              results=results,
                              pagination=pagination,
                              pending_counts=pending_counts,
                              superannuation_counts=get_superannuation_counts(),
                              search_query=search_query,
                              sort_by=sort_by,
                              sort_order=sort_order,
                              institution_filter=institution_filter,
                              designation_filter=designation_filter,
                              willingness_filter=willingness_filter,
                              present_status_filter=present_status_filter,
                              moc_filter=moc_filter,
                              major_minor_filter=major_minor_filter,
                              refunded_filter=refunded_filter,
                              finalised_filter=finalised_filter,
                              prelim_filter=prelim_filter,
                              rule15_filter=rule15_filter,
                              court_forum_filter=court_forum_filter,
                              court_status_filter=court_status_filter,
                              institutions=institutions,
                              designations=designations,
                              present_statuses=present_statuses,
                              court_forums=court_forums)
    
    elif tab == 'remarks':
        # Remarks tab - query RemarksEntry table
        query = RemarksEntry.query
        
        if search_query:
            query = query.filter(
                or_(
                    RemarksEntry.pen.ilike(f'%{search_query}%'),
                    RemarksEntry.name.ilike(f'%{search_query}%'),
                    RemarksEntry.remarks_file_no.ilike(f'%{search_query}%'),
                    RemarksEntry.institution.ilike(f'%{search_query}%')
                )
            )
        
        # Apply sorting for remarks tab
        if sort_by:
            sort_column = None
            if sort_by == 'name':
                sort_column = RemarksEntry.name
            elif sort_by == 'pen':
                sort_column = RemarksEntry.pen
            elif sort_by == 'section':
                sort_column = RemarksEntry.section
            elif sort_by == 'remarks_file_no':
                sort_column = RemarksEntry.remarks_file_no
            elif sort_by == 'institution':
                sort_column = RemarksEntry.institution
            elif sort_by == 'status':
                sort_column = RemarksEntry.status
            
            if sort_column is not None:
                if sort_order == 'desc':
                    query = query.order_by(sort_column.desc())
                else:
                    query = query.order_by(sort_column.asc())
            else:
                query = query.order_by(RemarksEntry.id.desc())
        else:
            query = query.order_by(RemarksEntry.id.desc())
        
        remarks_pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        results = remarks_pagination.items
        
        return render_template('disciplinary/index.html',
                              tab=tab,
                              inner_tab=inner_tab,
                              results=results,
                              pagination=pagination,
                              remarks_pagination=remarks_pagination,
                              search_query=search_query,
                              sort_by=sort_by,
                              sort_order=sort_order,
                              # Filter values
                              institution_filter=institution_filter,
                              designation_filter=designation_filter,
                              willingness_filter=willingness_filter,
                              present_status_filter=present_status_filter,
                              probation_status_filter=probation_status_filter,
                              group_by_designation=group_by_designation,
                              designation_stats=designation_stats,
                              moc_filter=moc_filter,
                              major_minor_filter=major_minor_filter,
                              refunded_filter=refunded_filter,
                              finalised_filter=finalised_filter,
                              prelim_filter=prelim_filter,
                              rule15_filter=rule15_filter,
                              court_forum_filter=court_forum_filter,
                              court_status_filter=court_status_filter,
                              # Filter options
                              institutions=institutions,
                              designations=designations,
                              present_statuses=present_statuses,
                              court_forums=court_forums,
                              superannuation_counts=None,
                              pending_counts=None)
    
    return render_template('disciplinary/index.html',
                          tab=tab,
                          inner_tab=inner_tab,
                          results=results,
                          pagination=pagination,
                          search_query=search_query,
                          sort_by=sort_by,
                          sort_order=sort_order,
                          # Filter values
                          institution_filter=institution_filter,
                          designation_filter=designation_filter,
                          willingness_filter=willingness_filter,
                          present_status_filter=present_status_filter,
                          probation_status_filter=probation_status_filter,
                          group_by_designation=group_by_designation,
                          designation_stats=designation_stats,
                          moc_filter=moc_filter,
                          major_minor_filter=major_minor_filter,
                          refunded_filter=refunded_filter,
                          finalised_filter=finalised_filter,
                          prelim_filter=prelim_filter,
                          rule15_filter=rule15_filter,
                          court_forum_filter=court_forum_filter,
                          court_status_filter=court_status_filter,
                          # Filter options
                          institutions=institutions,
                          designations=designations,
                          present_statuses=present_statuses,
                          court_forums=court_forums,
                          superannuation_counts=get_superannuation_counts() if tab in ['disciplinary', 'superannuation', 'pending_notices'] else None,
                          pending_counts=get_pending_counts() if tab in ['disciplinary', 'superannuation', 'pending_notices'] else None)


@disciplinary_bp.route('/list')
@login_required
def list_actions():
    """Redirect to list - for backward compatibility."""
    return redirect(url_for('disciplinary.list_disciplinary_actions'))


@disciplinary_bp.route('/')
@login_required
def list_disciplinary_actions():
    """List all disciplinary actions."""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Get filter parameters
    search_query = request.args.get('q', '').strip()
    status_filter = request.args.get('status', '')
    
    query = DisciplinaryAction.query
    
    if search_query:
        query = query.filter(
            or_(
                DisciplinaryAction.file_number.ilike(f'%{search_query}%'),
                DisciplinaryAction.pen.ilike(f'%{search_query}%'),
                DisciplinaryAction.employee_name.ilike(f'%{search_query}%'),
                DisciplinaryAction.institution.ilike(f'%{search_query}%')
            )
        )
    
    # Order by id (no created_at in desktop database)
    query = query.order_by(DisciplinaryAction.id.desc())
    
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    actions = pagination.items
    
    return render_template('disciplinary/list.html', 
                          actions=actions, 
                          pagination=pagination,
                          search_query=search_query,
                          status_filter=status_filter)


@disciplinary_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_disciplinary_action():
    """Create a new disciplinary action."""
    if request.method == 'POST':
        file_number = request.form.get('file_number', '').strip()
        
        if not file_number:
            flash('File number is required.', 'danger')
            return render_template('disciplinary/create.html')
        
        # Check if file exists
        file = File.query.filter_by(file_number=file_number).first()
        if not file:
            flash(f'File "{file_number}" does not exist.', 'danger')
            return render_template('disciplinary/create.html')
        
        da = DisciplinaryAction(
            file_number=file_number,
            employee_name=request.form.get('employee_name', ''),
            pen=request.form.get('pen', ''),
            designation=request.form.get('designation', ''),
            institution=request.form.get('institution', ''),
            entry_cadre=request.form.get('entry_cadre', ''),
            joining_date=request.form.get('joining_date', ''),
            service_regularised=request.form.get('service_regularised', ''),
            date_regularisation=request.form.get('date_regularisation', ''),
            probation=request.form.get('probation', ''),
            date_probation_declared=request.form.get('date_probation_declared', ''),
            date_superannuation=request.form.get('date_superannuation', ''),
            unauthorised_others=request.form.get('unauthorised_others', ''),
            probation_termination_notice=request.form.get('probation_termination_notice', ''),
            ptn_reply_received=request.form.get('ptn_reply_received', ''),
            ptn_reply_date=request.form.get('ptn_reply_date', ''),
            action_taking_office=request.form.get('action_taking_office', ''),
            moc_issued=request.form.get('moc_issued', ''),
            moc_issued_by=request.form.get('moc_issued_by', ''),
            major_minor=request.form.get('major_minor', ''),
            moc_number=request.form.get('moc_number', ''),
            moc_date=request.form.get('moc_date', ''),
            moc_receipt_date=request.form.get('moc_receipt_date', ''),
            wsd_received_date=request.form.get('wsd_received_date', ''),
            wsd_letter_no=request.form.get('wsd_letter_no', ''),
            scn_issued_date=request.form.get('scn_issued_date', ''),
            scn_issued_by=request.form.get('scn_issued_by', ''),
            scn_receipt_date=request.form.get('scn_receipt_date', ''),
            scn_receipt_sent_to_dhs_date=request.form.get('scn_receipt_sent_to_dhs_date', ''),
            scn_reply_date=request.form.get('scn_reply_date', ''),
            moc_received_at_dmo_date=request.form.get('moc_received_at_dmo_date', ''),
            moc_received_letter_no=request.form.get('moc_received_letter_no', ''),
            moc_sent_to_dhs_date=request.form.get('moc_sent_to_dhs_date', ''),
            wsd_sent_to_dhs_date=request.form.get('wsd_sent_to_dhs_date', ''),
            wsd_sent_letter_no=request.form.get('wsd_sent_letter_no', ''),
            scn_received_at_dmo_date=request.form.get('scn_received_at_dmo_date', ''),
            scn_reply_sent_to_dhs_date=request.form.get('scn_reply_sent_to_dhs_date', ''),
            dhs_file_number=request.form.get('dhs_file_number', ''),
            finalised_date=request.form.get('finalised_date', '')
        )
        
        db.session.add(da)
        db.session.commit()
        
        # If unauthorised absentee, add UA details
        if request.form.get('unauthorised_others') == 'Unauthorised':
            ua = UnauthorisedAbsentee(
                da_id=da.id,
                date_from_ua=request.form.get('date_from_ua', ''),
                willingness=request.form.get('willingness', ''),
                bond_submitted=request.form.get('bond_submitted', ''),
                communication_address=request.form.get('communication_address', ''),
                date_reported_to_dmo=request.form.get('date_reported_to_dmo', ''),
                letter_no_reported_to_dmo=request.form.get('letter_no_reported_to_dmo', ''),
                date_reported_to_dhs=request.form.get('date_reported_to_dhs', ''),
                letter_no_reported_to_dhs=request.form.get('letter_no_reported_to_dhs', ''),
                weather_reported_to_dhs=request.form.get('weather_reported_to_dhs', ''),
                present_status=request.form.get('present_status', ''),
                disc_action_status=request.form.get('disc_action_status', '')
            )
            db.session.add(ua)
            db.session.commit()
        
        flash('Disciplinary action created successfully.', 'success')
        # Stay on the DA window for this file
        return redirect(url_for('disciplinary.create_disciplinary_action', file_number=file_number))
    
    # Get file number from query params if provided
    file_number = request.args.get('file_number', '')
    
    # Get existing DA entries for this file
    existing_entries = []
    if file_number:
        existing_entries = DisciplinaryAction.query.filter_by(file_number=file_number).order_by(DisciplinaryAction.id.desc()).all()
    
    return render_template('disciplinary/create.html', file_number=file_number, existing_entries=existing_entries)


@disciplinary_bp.route('/<int:id>/json')
@login_required
def get_da_json(id):
    """Get DA entry as JSON for AJAX loading."""
    action = DisciplinaryAction.query.get_or_404(id)
    ua_details = UnauthorisedAbsentee.query.filter_by(da_id=id).first()
    
    data = {
        'id': action.id,
        'file_number': action.file_number or '',
        'employee_name': action.employee_name or '',
        'pen': action.pen or '',
        'designation': action.designation or '',
        'institution': action.institution or '',
        'entry_cadre': action.entry_cadre or '',
        'joining_date': action.joining_date or '',
        'service_regularised': action.service_regularised or '',
        'date_regularisation': action.date_regularisation or '',
        'probation': action.probation or '',
        'date_probation_declared': action.date_probation_declared or '',
        'date_superannuation': action.date_superannuation or '',
        'unauthorised_others': action.unauthorised_others or '',
        'probation_termination_notice': action.probation_termination_notice or '',
        'ptn_reply_received': action.ptn_reply_received or '',
        'ptn_reply_date': action.ptn_reply_date or '',
        'action_taking_office': action.action_taking_office or '',
        'moc_issued': action.moc_issued or '',
        'moc_issued_by': action.moc_issued_by or '',
        'major_minor': action.major_minor or '',
        'moc_number': action.moc_number or '',
        'moc_date': action.moc_date or '',
        'moc_receipt_date': action.moc_receipt_date or '',
        'moc_received_at_dmo_date': action.moc_received_at_dmo_date or '',
        'moc_received_letter_no': action.moc_received_letter_no or '',
        'moc_sent_to_dhs_date': action.moc_sent_to_dhs_date or '',
        'wsd_received_date': action.wsd_received_date or '',
        'wsd_letter_no': action.wsd_letter_no or '',
        'wsd_sent_to_dhs_date': action.wsd_sent_to_dhs_date or '',
        'wsd_sent_letter_no': action.wsd_sent_letter_no or '',
        'scn_issued_date': action.scn_issued_date or '',
        'scn_issued_by': action.scn_issued_by or '',
        'scn_receipt_date': action.scn_receipt_date or '',
        'scn_receipt_sent_to_dhs_date': action.scn_receipt_sent_to_dhs_date or '',
        'scn_received_at_dmo_date': action.scn_received_at_dmo_date or '',
        'scn_reply_date': action.scn_reply_date or '',
        'scn_reply_sent_to_dhs_date': action.scn_reply_sent_to_dhs_date or '',
        'dhs_file_number': action.dhs_file_number or '',
        'finalised_date': action.finalised_date or ''
    }
    
    # Add UA details if present
    if ua_details:
        data.update({
            'date_from_ua': ua_details.date_from_ua or '',
            'willingness': ua_details.willingness or '',
            'bond_submitted': ua_details.bond_submitted or '',
            'communication_address': ua_details.communication_address or '',
            'date_reported_to_dmo': ua_details.date_reported_to_dmo or '',
            'letter_no_reported_to_dmo': ua_details.letter_no_reported_to_dmo or '',
            'date_reported_to_dhs': ua_details.date_reported_to_dhs or '',
            'letter_no_reported_to_dhs': ua_details.letter_no_reported_to_dhs or '',
            'weather_reported_to_dhs': ua_details.weather_reported_to_dhs or '',
            'present_status': ua_details.present_status or '',
            'disc_action_status': ua_details.disc_action_status or ''
        })
    
    return jsonify({'success': True, 'entry': data})


@disciplinary_bp.route('/<int:id>')
@login_required
def view_action(id):
    """View disciplinary action details."""
    action = DisciplinaryAction.query.get_or_404(id)
    ua_details = UnauthorisedAbsentee.query.filter_by(da_id=id).first()
    
    return render_template('disciplinary/view.html', action=action, ua_details=ua_details)


@disciplinary_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_action(id):
    """Edit disciplinary action."""
    action = DisciplinaryAction.query.get_or_404(id)
    ua_details = UnauthorisedAbsentee.query.filter_by(da_id=id).first()
    
    if request.method == 'POST':
        action.employee_name = request.form.get('employee_name', '')
        action.pen = request.form.get('pen', '')
        action.designation = request.form.get('designation', '')
        action.institution = request.form.get('institution', '')
        action.entry_cadre = request.form.get('entry_cadre', '')
        action.joining_date = request.form.get('joining_date', '')
        action.service_regularised = request.form.get('service_regularised', '')
        action.date_regularisation = request.form.get('date_regularisation', '')
        action.probation = request.form.get('probation', '')
        action.date_probation_declared = request.form.get('date_probation_declared', '')
        action.date_superannuation = request.form.get('date_superannuation', '')
        action.unauthorised_others = request.form.get('unauthorised_others', '')
        action.probation_termination_notice = request.form.get('probation_termination_notice', '')
        action.ptn_reply_received = request.form.get('ptn_reply_received', '')
        action.ptn_reply_date = request.form.get('ptn_reply_date', '')
        action.action_taking_office = request.form.get('action_taking_office', '')
        action.moc_issued = request.form.get('moc_issued', '')
        action.moc_issued_by = request.form.get('moc_issued_by', '')
        action.major_minor = request.form.get('major_minor', '')
        action.moc_number = request.form.get('moc_number', '')
        action.moc_date = request.form.get('moc_date', '')
        action.moc_receipt_date = request.form.get('moc_receipt_date', '')
        action.wsd_received_date = request.form.get('wsd_received_date', '')
        action.wsd_letter_no = request.form.get('wsd_letter_no', '')
        action.scn_issued_date = request.form.get('scn_issued_date', '')
        action.scn_issued_by = request.form.get('scn_issued_by', '')
        action.scn_receipt_date = request.form.get('scn_receipt_date', '')
        action.scn_receipt_sent_to_dhs_date = request.form.get('scn_receipt_sent_to_dhs_date', '')
        action.scn_reply_date = request.form.get('scn_reply_date', '')
        action.moc_received_at_dmo_date = request.form.get('moc_received_at_dmo_date', '')
        action.moc_received_letter_no = request.form.get('moc_received_letter_no', '')
        action.moc_sent_to_dhs_date = request.form.get('moc_sent_to_dhs_date', '')
        action.wsd_sent_to_dhs_date = request.form.get('wsd_sent_to_dhs_date', '')
        action.wsd_sent_letter_no = request.form.get('wsd_sent_letter_no', '')
        action.scn_received_at_dmo_date = request.form.get('scn_received_at_dmo_date', '')
        action.scn_reply_sent_to_dhs_date = request.form.get('scn_reply_sent_to_dhs_date', '')
        action.dhs_file_number = request.form.get('dhs_file_number', '')
        action.finalised_date = request.form.get('finalised_date', '')
        
        # Update or create UA details
        if request.form.get('unauthorised_others') == 'Unauthorised':
            if ua_details:
                ua_details.date_from_ua = request.form.get('date_from_ua', '')
                ua_details.willingness = request.form.get('willingness', '')
                ua_details.bond_submitted = request.form.get('bond_submitted', '')
                ua_details.communication_address = request.form.get('communication_address', '')
                ua_details.date_reported_to_dmo = request.form.get('date_reported_to_dmo', '')
                ua_details.letter_no_reported_to_dmo = request.form.get('letter_no_reported_to_dmo', '')
                ua_details.date_reported_to_dhs = request.form.get('date_reported_to_dhs', '')
                ua_details.letter_no_reported_to_dhs = request.form.get('letter_no_reported_to_dhs', '')
                ua_details.weather_reported_to_dhs = request.form.get('weather_reported_to_dhs', '')
                ua_details.present_status = request.form.get('present_status', '')
                ua_details.disc_action_status = request.form.get('disc_action_status', '')
            else:
                ua = UnauthorisedAbsentee(
                    da_id=action.id,
                    date_from_ua=request.form.get('date_from_ua', ''),
                    willingness=request.form.get('willingness', ''),
                    bond_submitted=request.form.get('bond_submitted', ''),
                    communication_address=request.form.get('communication_address', ''),
                    date_reported_to_dmo=request.form.get('date_reported_to_dmo', ''),
                    letter_no_reported_to_dmo=request.form.get('letter_no_reported_to_dmo', ''),
                    date_reported_to_dhs=request.form.get('date_reported_to_dhs', ''),
                    letter_no_reported_to_dhs=request.form.get('letter_no_reported_to_dhs', ''),
                    weather_reported_to_dhs=request.form.get('weather_reported_to_dhs', ''),
                    present_status=request.form.get('present_status', ''),
                    disc_action_status=request.form.get('disc_action_status', '')
                )
                db.session.add(ua)
        
        db.session.commit()
        
        flash('Disciplinary action updated successfully.', 'success')
        # Stay on the DA window for this file
        return redirect(url_for('disciplinary.create_disciplinary_action', file_number=action.file_number))
    
    return render_template('disciplinary/edit.html', action=action, ua_details=ua_details)


@disciplinary_bp.route('/<int:id>/edit-da', methods=['POST'])
@login_required
def edit_disciplinary_action(id):
    """Edit disciplinary action (from the create page form)."""
    action = DisciplinaryAction.query.get_or_404(id)
    ua_details = UnauthorisedAbsentee.query.filter_by(da_id=id).first()
    
    action.employee_name = request.form.get('employee_name', '')
    action.pen = request.form.get('pen', '')
    action.designation = request.form.get('designation', '')
    action.institution = request.form.get('institution', '')
    action.entry_cadre = request.form.get('entry_cadre', '')
    action.joining_date = request.form.get('joining_date', '')
    action.service_regularised = request.form.get('service_regularised', '')
    action.date_regularisation = request.form.get('date_regularisation', '')
    action.probation = request.form.get('probation', '')
    action.date_probation_declared = request.form.get('date_probation_declared', '')
    action.date_superannuation = request.form.get('date_superannuation', '')
    action.unauthorised_others = request.form.get('unauthorised_others', '')
    action.probation_termination_notice = request.form.get('probation_termination_notice', '')
    action.ptn_reply_received = request.form.get('ptn_reply_received', '')
    action.ptn_reply_date = request.form.get('ptn_reply_date', '')
    action.action_taking_office = request.form.get('action_taking_office', '')
    action.moc_issued = request.form.get('moc_issued', '')
    action.moc_issued_by = request.form.get('moc_issued_by', '')
    action.major_minor = request.form.get('major_minor', '')
    action.moc_number = request.form.get('moc_number', '')
    action.moc_date = request.form.get('moc_date', '')
    action.moc_receipt_date = request.form.get('moc_receipt_date', '')
    action.wsd_received_date = request.form.get('wsd_received_date', '')
    action.wsd_letter_no = request.form.get('wsd_letter_no', '')
    action.scn_issued_date = request.form.get('scn_issued_date', '')
    action.scn_issued_by = request.form.get('scn_issued_by', '')
    action.scn_receipt_date = request.form.get('scn_receipt_date', '')
    action.scn_receipt_sent_to_dhs_date = request.form.get('scn_receipt_sent_to_dhs_date', '')
    action.scn_reply_date = request.form.get('scn_reply_date', '')
    action.moc_received_at_dmo_date = request.form.get('moc_received_at_dmo_date', '')
    action.moc_received_letter_no = request.form.get('moc_received_letter_no', '')
    action.moc_sent_to_dhs_date = request.form.get('moc_sent_to_dhs_date', '')
    action.wsd_sent_to_dhs_date = request.form.get('wsd_sent_to_dhs_date', '')
    action.wsd_sent_letter_no = request.form.get('wsd_sent_letter_no', '')
    action.scn_received_at_dmo_date = request.form.get('scn_received_at_dmo_date', '')
    action.scn_reply_sent_to_dhs_date = request.form.get('scn_reply_sent_to_dhs_date', '')
    action.dhs_file_number = request.form.get('dhs_file_number', '')
    action.finalised_date = request.form.get('finalised_date', '')
    
    # Update or create UA details
    if request.form.get('unauthorised_others') == 'Unauthorised':
        if ua_details:
            ua_details.date_from_ua = request.form.get('date_from_ua', '')
            ua_details.willingness = request.form.get('willingness', '')
            ua_details.bond_submitted = request.form.get('bond_submitted', '')
            ua_details.communication_address = request.form.get('communication_address', '')
            ua_details.date_reported_to_dmo = request.form.get('date_reported_to_dmo', '')
            ua_details.letter_no_reported_to_dmo = request.form.get('letter_no_reported_to_dmo', '')
            ua_details.date_reported_to_dhs = request.form.get('date_reported_to_dhs', '')
            ua_details.letter_no_reported_to_dhs = request.form.get('letter_no_reported_to_dhs', '')
            ua_details.weather_reported_to_dhs = request.form.get('weather_reported_to_dhs', '')
            ua_details.present_status = request.form.get('present_status', '')
            ua_details.disc_action_status = request.form.get('disc_action_status', '')
        else:
            ua = UnauthorisedAbsentee(
                da_id=action.id,
                date_from_ua=request.form.get('date_from_ua', ''),
                willingness=request.form.get('willingness', ''),
                bond_submitted=request.form.get('bond_submitted', ''),
                communication_address=request.form.get('communication_address', ''),
                date_reported_to_dmo=request.form.get('date_reported_to_dmo', ''),
                letter_no_reported_to_dmo=request.form.get('letter_no_reported_to_dmo', ''),
                date_reported_to_dhs=request.form.get('date_reported_to_dhs', ''),
                letter_no_reported_to_dhs=request.form.get('letter_no_reported_to_dhs', ''),
                weather_reported_to_dhs=request.form.get('weather_reported_to_dhs', ''),
                present_status=request.form.get('present_status', ''),
                disc_action_status=request.form.get('disc_action_status', '')
            )
            db.session.add(ua)
    
    db.session.commit()
    
    flash('Disciplinary action updated successfully.', 'success')
    return redirect(url_for('disciplinary.create_disciplinary_action', file_number=action.file_number))


@disciplinary_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete_action(id):
    """Delete disciplinary action."""
    action = DisciplinaryAction.query.get_or_404(id)
    file_number = action.file_number
    
    db.session.delete(action)
    db.session.commit()
    
    flash('Disciplinary action entry deleted successfully.', 'success')
    return redirect(url_for('disciplinary.create_disciplinary_action', file_number=file_number))


@disciplinary_bp.route('/ua-list')
@login_required
def ua_list():
    """List all unauthorised absentees."""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    query = db.session.query(DisciplinaryAction, UnauthorisedAbsentee).join(
        UnauthorisedAbsentee, DisciplinaryAction.id == UnauthorisedAbsentee.da_id
    )
    
    search_query = request.args.get('q', '').strip()
    if search_query:
        query = query.filter(
            or_(
                DisciplinaryAction.pen.ilike(f'%{search_query}%'),
                DisciplinaryAction.employee_name.ilike(f'%{search_query}%'),
                DisciplinaryAction.institution.ilike(f'%{search_query}%')
            )
        )
    
    query = query.order_by(DisciplinaryAction.id.desc())
    
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    results = pagination.items
    
    return render_template('disciplinary/ua_list.html', 
                          results=results, 
                          pagination=pagination,
                          search_query=search_query)


@disciplinary_bp.route('/api/get-employee/<pen>')
@login_required
def api_get_employee(pen):
    """API endpoint to get employee details by PEN."""
    employee = Employee.query.filter_by(pen=pen).first()
    
    if employee:
        return jsonify({
            'success': True,
            'employee': {
                'name': employee.name or '',
                'designation': employee.designation or '',
                'institution': employee.institution_name or '',
                'joining_date': employee.joining_date or '',
                'date_of_birth': employee.date_of_birth or ''
            }
        })
    else:
        return jsonify({'success': False, 'employee': None})


@disciplinary_bp.route('/api/get-institutions')
@login_required
def api_get_institutions():
    """API endpoint to get all institution names for autocomplete."""
    institutions = db.session.query(Institution.name).filter(
        Institution.name != None, Institution.name != ''
    ).distinct().order_by(Institution.name.asc()).all()
    
    institution_names = [i[0] for i in institutions]
    return jsonify({'success': True, 'institutions': institution_names})


# ========================
# Remarks Tab Routes
# ========================

@disciplinary_bp.route('/api/check-pen-status/<pen>')
@login_required
def api_check_pen_status(pen):
    """API endpoint to check if PEN exists in disciplinary proceedings."""
    # Check if PEN exists in disciplinary_action_details
    exists = DisciplinaryAction.query.filter_by(pen=pen).first() is not None
    return jsonify({'exists': exists})


@disciplinary_bp.route('/remarks/create', methods=['POST'])
@login_required
def create_remarks_entry():
    """Create a new remarks entry."""
    entry = RemarksEntry(
        section=request.form.get('section', ''),
        remarks_file_no=request.form.get('remarks_file_no', ''),
        pen=request.form.get('pen', ''),
        prefix=request.form.get('prefix', ''),
        name=request.form.get('name', ''),
        designation=request.form.get('designation', ''),
        institution=request.form.get('institution', ''),
        status=request.form.get('status', 'Clear'),
        created_at=datetime.now().isoformat()
    )
    
    db.session.add(entry)
    db.session.commit()
    
    flash('Remarks entry created successfully.', 'success')
    return redirect(url_for('disciplinary.index', tab='remarks'))


@disciplinary_bp.route('/remarks/<int:id>/json')
@login_required
def get_remarks_json(id):
    """Get remarks entry as JSON for AJAX loading."""
    entry = RemarksEntry.query.get_or_404(id)
    
    data = {
        'id': entry.id,
        'section': entry.section or '',
        'remarks_file_no': entry.remarks_file_no or '',
        'pen': entry.pen or '',
        'prefix': entry.prefix or '',
        'name': entry.name or '',
        'designation': entry.designation or '',
        'institution': entry.institution or '',
        'status': entry.status or 'Clear',
        'created_at': entry.created_at or ''
    }
    
    return jsonify({'success': True, 'entry': data})


@disciplinary_bp.route('/remarks/<int:id>/edit', methods=['POST'])
@login_required
def edit_remarks_entry(id):
    """Edit an existing remarks entry."""
    entry = RemarksEntry.query.get_or_404(id)
    
    entry.section = request.form.get('section', '')
    entry.remarks_file_no = request.form.get('remarks_file_no', '')
    entry.pen = request.form.get('pen', '')
    entry.prefix = request.form.get('prefix', '')
    entry.name = request.form.get('name', '')
    entry.designation = request.form.get('designation', '')
    entry.institution = request.form.get('institution', '')
    entry.status = request.form.get('status', 'Clear')
    
    db.session.commit()
    
    flash('Remarks entry updated successfully.', 'success')
    return redirect(url_for('disciplinary.index', tab='remarks'))


@disciplinary_bp.route('/remarks/<int:id>/delete', methods=['POST'])
@login_required
def delete_remarks_entry(id):
    """Delete a remarks entry."""
    entry = RemarksEntry.query.get_or_404(id)
    
    db.session.delete(entry)
    db.session.commit()
    
    flash('Remarks entry deleted successfully.', 'success')
    return redirect(url_for('disciplinary.index', tab='remarks'))


@disciplinary_bp.route('/remarks/export')
@login_required
def export_remarks():
    """Export remarks entries to CSV/Excel format."""
    entries = RemarksEntry.query.order_by(RemarksEntry.id.desc()).all()
    
    # Create CSV in memory
    output = io.StringIO()
    # Add UTF-8 BOM for Excel to recognize Unicode characters (Malayalam etc.)
    output.write('\ufeff')
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['Sl. No.', 'Section', 'Remarks File No.', 'PEN', 'Prefix', 'Name', 'Designation', 'Institution', 'Status', 'Created At'])
    
    # Write data
    for idx, entry in enumerate(entries, 1):
        writer.writerow([
            idx,
            entry.section or '',
            entry.remarks_file_no or '',
            entry.pen or '',
            entry.prefix or '',
            entry.name or '',
            entry.designation or '',
            entry.institution or '',
            entry.status or '',
            entry.created_at or ''
        ])
    
    # Create response
    output.seek(0)
    return Response(
        output.getvalue().encode('utf-8-sig'),
        mimetype='text/csv; charset=utf-8-sig',
        headers={'Content-Disposition': f'attachment; filename=Remarks_Export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'}
    )


@disciplinary_bp.route('/superannuation/export')
@login_required
def export_superannuation():
    """Export superannuation data to CSV (matching desktop app export)."""
    inner_tab = request.args.get('inner_tab', 'within_1_year')
    
    # Get all non-finalized DA records with employee data using raw SQL
    sql = text("""
        SELECT d.id as da_id, d.pen, d.file_number, d.employee_name, d.designation, d.institution,
               d.date_superannuation, e.date_of_birth, e.name, e.designation AS emp_designation,
               e.institution_name AS emp_institution
        FROM disciplinary_action_details d
        LEFT JOIN employees e ON d.pen = e.pen
        WHERE d.pen IS NOT NULL AND d.pen != ''
        AND (d.finalised_date IS NULL OR d.finalised_date = '')
    """)
    
    da_records = db.session.execute(sql).fetchall()
    
    today = datetime.now()
    one_year_future = today + timedelta(days=365)
    two_years_future = today + timedelta(days=730)
    
    results = []
    
    for record in da_records:
        da_id, pen, file_number, da_name, da_designation, da_institution, da_super_date, emp_dob, emp_name, emp_designation, emp_institution = record
        
        # Determine superannuation date
        superannuation_date = None
        if da_super_date and str(da_super_date).strip():
            for fmt in ['%d-%m-%Y', '%Y-%m-%d', '%d/%m/%Y']:
                try:
                    superannuation_date = datetime.strptime(str(da_super_date).strip(), fmt)
                    break
                except:
                    continue
        
        if not superannuation_date and emp_dob and str(emp_dob).strip():
            try:
                dob = datetime.strptime(str(emp_dob).strip(), '%d-%m-%Y')
                superannuation_date = dob.replace(year=dob.year + 60)
            except:
                pass
        
        if not superannuation_date:
            continue
        
        # Filter based on inner_tab
        include_record = False
        days_value = 0
        
        if inner_tab == 'within_1_year':
            if today <= superannuation_date <= one_year_future:
                include_record = True
                days_value = (superannuation_date - today).days
        elif inner_tab == 'within_2_years':
            if one_year_future < superannuation_date <= two_years_future:
                include_record = True
                days_value = (superannuation_date - today).days
        elif inner_tab == 'retired':
            if superannuation_date < today:
                include_record = True
                days_value = (today - superannuation_date).days
        
        if include_record:
            results.append({
                'file_number': file_number or '',
                'pen': pen,
                'name': emp_name or da_name or '',
                'designation': emp_designation or da_designation or '',
                'institution': emp_institution or da_institution or '',
                'date_of_birth': str(emp_dob) if emp_dob else '',
                'superannuation_date': superannuation_date.strftime('%d-%m-%Y'),
                'days': days_value
            })
    
    # Sort by superannuation date
    if inner_tab == 'retired':
        results.sort(key=lambda x: datetime.strptime(x['superannuation_date'], '%d-%m-%Y'), reverse=True)
    else:
        results.sort(key=lambda x: datetime.strptime(x['superannuation_date'], '%d-%m-%Y'))
    
    # Create CSV in memory
    output = io.StringIO()
    # Add UTF-8 BOM for Excel to recognize Unicode characters (Malayalam etc.)
    output.write('\ufeff')
    writer = csv.writer(output)
    
    # Write header
    days_col = 'Days Since Retirement' if inner_tab == 'retired' else 'Days Remaining'
    writer.writerow(['Sl. No.', 'File Number', 'PEN', 'Name', 'Designation', 'Date of Birth', 
                     'Superannuation Date', 'Institution', days_col])
    
    # Write data
    for idx, item in enumerate(results, 1):
        writer.writerow([
            idx,
            item['file_number'],
            item['pen'],
            item['name'],
            item['designation'],
            item['date_of_birth'],
            item['superannuation_date'],
            item['institution'],
            item['days']
        ])
    
    # Map inner_tab to filename
    tab_names = {
        'within_1_year': 'Within_1_Year',
        'within_2_years': 'Within_2_Years',
        'retired': 'Retired'
    }
    
    # Create response
    output.seek(0)
    return Response(
        output.getvalue().encode('utf-8-sig'),
        mimetype='text/csv; charset=utf-8-sig',
        headers={'Content-Disposition': f'attachment; filename=Superannuation_{tab_names.get(inner_tab, "Export")}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'}
    )


@disciplinary_bp.route('/pending_notices/export')
@login_required
def export_pending_notices():
    """Export pending notices data to CSV (matching desktop app export)."""
    inner_tab = request.args.get('inner_tab', 'moc_dmo')
    
    # Get migrated and closed files to exclude
    migrated_sql = text("""
        SELECT file_number FROM files WHERE file_type = 'Physical' OR file_type = 'Physical File'
    """)
    closed_sql = text("""
        SELECT file_number FROM files WHERE is_closed = 1
    """)
    
    try:
        migrated_files = {str(row[0]).strip() for row in db.session.execute(migrated_sql).fetchall() if row[0]}
    except:
        migrated_files = set()
    
    try:
        closed_files = {str(row[0]).strip() for row in db.session.execute(closed_sql).fetchall() if row[0]}
    except:
        closed_files = set()
    
    # Get all disciplinary action details
    da_sql = text("""
        SELECT id, file_number, pen, employee_name, designation, institution,
               action_taking_office, moc_issued, moc_date, moc_receipt_date, wsd_received_date,
               probation_termination_notice, scn_issued_date, scn_receipt_date, scn_reply_date
        FROM disciplinary_action_details
        WHERE (finalised_date IS NULL OR finalised_date = '')
    """)
    
    da_records = db.session.execute(da_sql).fetchall()
    
    pending_results = []
    today = datetime.now()
    
    for record in da_records:
        (da_id, file_number, pen, employee_name, designation, institution,
         action_taking_office, moc_issued, moc_date, moc_receipt_date, wsd_received_date,
         ptn, scn_issued_date, scn_receipt_date, scn_reply_date) = record
        
        # Skip migrated and closed files
        file_num_str = str(file_number).strip() if file_number else ''
        if file_num_str in migrated_files or file_num_str in closed_files:
            continue
        
        include_record = False
        issued_date = None
        
        # Normalize values
        action_office = str(action_taking_office).strip().upper() if action_taking_office else ''
        moc_issued_val = str(moc_issued).strip().lower() if moc_issued else ''
        moc_date_str = str(moc_date).strip() if moc_date else ''
        moc_receipt_str = str(moc_receipt_date).strip() if moc_receipt_date else ''
        wsd_received_str = str(wsd_received_date).strip() if wsd_received_date else ''
        ptn_val = str(ptn).strip().lower() if ptn else ''
        scn_issued_str = str(scn_issued_date).strip() if scn_issued_date else ''
        scn_receipt_str = str(scn_receipt_date).strip() if scn_receipt_date else ''
        scn_reply_str = str(scn_reply_date).strip() if scn_reply_date else ''
        
        # Check based on inner_tab
        if inner_tab == 'moc_dmo':
            if moc_issued_val == 'issued' and action_office == 'DMO' and not moc_receipt_str:
                include_record = True
                issued_date = moc_date_str
        elif inner_tab == 'moc_dhs':
            if moc_issued_val == 'issued' and (action_office == 'DHS' or action_office == 'DHS/GOVT') and not moc_receipt_str:
                include_record = True
                issued_date = moc_date_str
        elif inner_tab == 'ptn_dmo':
            if ptn_val == 'issued' and action_office == 'DMO' and not scn_receipt_str:
                include_record = True
                issued_date = scn_issued_str
        elif inner_tab == 'ptn_dhs':
            if ptn_val == 'issued' and (action_office == 'DHS' or action_office == 'DHS/GOVT') and not scn_receipt_str:
                include_record = True
                issued_date = scn_issued_str
        elif inner_tab == 'scn_dmo':
            if scn_issued_str and action_office == 'DMO' and not scn_receipt_str:
                include_record = True
                issued_date = scn_issued_str
        elif inner_tab == 'scn_dhs':
            if scn_issued_str and (action_office == 'DHS' or action_office == 'DHS/GOVT') and not scn_receipt_str:
                include_record = True
                issued_date = scn_issued_str
        elif inner_tab == 'wsd_pending':
            if moc_issued_val == 'issued' and moc_receipt_str and not wsd_received_str:
                include_record = True
                issued_date = moc_receipt_str
        elif inner_tab == 'scn_reply':
            if scn_issued_str and scn_receipt_str and not scn_reply_str:
                include_record = True
                issued_date = scn_receipt_str
        
        if include_record:
            # Calculate due date
            due_date = ''
            days_overdue = 0
            is_overdue = False
            
            if issued_date:
                for fmt in ['%d-%m-%Y', '%Y-%m-%d', '%d/%m/%Y']:
                    try:
                        issued_date_obj = datetime.strptime(issued_date, fmt)
                        due_date_obj = issued_date_obj + timedelta(days=15)
                        due_date = due_date_obj.strftime('%d-%m-%Y')
                        if today > due_date_obj:
                            is_overdue = True
                            days_overdue = (today - due_date_obj).days
                        break
                    except:
                        continue
            
            pending_results.append({
                'file_number': file_number or '',
                'pen': pen or '',
                'employee_name': employee_name or '',
                'designation': designation or '',
                'institution': institution or '',
                'issued_date': issued_date or '',
                'due_date': due_date,
                'days_overdue': days_overdue if is_overdue else 0,
                'is_overdue': is_overdue
            })
    
    # Sort by days overdue (descending)
    pending_results.sort(key=lambda x: (not x['is_overdue'], -x['days_overdue']))
    
    # Create CSV
    output = io.StringIO()
    # Add UTF-8 BOM for Excel to recognize Unicode characters (Malayalam etc.)
    output.write('\ufeff')
    writer = csv.writer(output)
    
    # Header row with tab-specific columns
    if inner_tab in ['moc_dmo', 'moc_dhs']:
        headers = ['Sl. No.', 'File Number', 'PEN', 'Employee Name', 'Designation', 'Institution', 
                   'MOC Issued Date', 'Receipt Due Date', 'Days Overdue']
    elif inner_tab in ['ptn_dmo', 'ptn_dhs']:
        headers = ['Sl. No.', 'File Number', 'PEN', 'Employee Name', 'Designation', 'Institution', 
                   'PTN Issued Date', 'Receipt Due Date', 'Days Overdue']
    elif inner_tab in ['scn_dmo', 'scn_dhs']:
        headers = ['Sl. No.', 'File Number', 'PEN', 'Employee Name', 'Designation', 'Institution', 
                   'SCN Issued Date', 'Receipt Due Date', 'Days Overdue']
    elif inner_tab == 'wsd_pending':
        headers = ['Sl. No.', 'File Number', 'PEN', 'Employee Name', 'Designation', 'Institution', 
                   'MOC Receipt Date', 'WSD Due Date', 'Days Overdue']
    elif inner_tab == 'scn_reply':
        headers = ['Sl. No.', 'File Number', 'PEN', 'Employee Name', 'Designation', 'Institution', 
                   'SCN Receipt Date', 'Reply Due Date', 'Days Overdue']
    else:
        headers = ['Sl. No.', 'File Number', 'PEN', 'Employee Name', 'Designation', 'Institution', 
                   'Issued Date', 'Due Date', 'Days Overdue']
    
    writer.writerow(headers)
    
    # Data rows
    for idx, item in enumerate(pending_results, 1):
        writer.writerow([
            idx,
            item['file_number'],
            item['pen'],
            item['employee_name'],
            item['designation'],
            item['institution'],
            item['issued_date'],
            item['due_date'],
            item['days_overdue'] if item['is_overdue'] else '-'
        ])
    
    # Map inner_tab to filename
    tab_names = {
        'moc_dmo': 'MOC_From_DMO',
        'moc_dhs': 'MOC_From_DHS',
        'ptn_dmo': 'PTN_From_DMO',
        'ptn_dhs': 'PTN_From_DHS',
        'scn_dmo': 'SCN_From_DMO',
        'scn_dhs': 'SCN_From_DHS',
        'wsd_pending': 'WSD_Pending',
        'scn_reply': 'SCN_Reply_Pending'
    }
    
    # Create response
    output.seek(0)
    return Response(
        output.getvalue().encode('utf-8-sig'),
        mimetype='text/csv; charset=utf-8-sig',
        headers={'Content-Disposition': f'attachment; filename=Pending_Notices_{tab_names.get(inner_tab, "Export")}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'}
    )

