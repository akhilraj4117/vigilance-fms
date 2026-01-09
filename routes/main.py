"""
Main routes for the Flask application.
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from models import File, DisciplinaryAction, RTIApplication, CourtCase, Employee, Institution, InquiryDetails, ReportSoughtDetails
from extensions import db
from sqlalchemy import func, or_, and_
import json

main_bp = Blueprint('main', __name__)


@main_bp.route('/fix-db-sequences')
@login_required
def fix_db_sequences():
    """Fix PostgreSQL sequences - accessible by any logged in user."""
    try:
        # Fix all table sequences
        tables = [
            'disciplinary_action_details',
            'unauthorised_absentee_details',
            'unauthorised_absentees',
            'rti_application_details',
            'court_case_details',
            'inquiry_details',
            'report_sought_details',
            'report_asked_details',
            'communication_details',
            'social_security_pension_details',
            'pr_entry_details',
            'employees',
            'institutions'
        ]
        
        fixed = 0
        for table in tables:
            try:
                # Get max ID
                result = db.session.execute(
                    db.text(f"SELECT MAX(id) FROM {table}")
                ).scalar()
                
                if result:
                    # Reset sequence
                    db.session.execute(
                        db.text(f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), {result}, true)")
                    )
                    fixed += 1
            except:
                pass
        
        db.session.commit()
        flash(f'Database sequences reset successfully ({fixed} tables fixed).', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'danger')
    
    return redirect(url_for('main.dashboard'))


@main_bp.route('/')
def index():
    """Home page - redirect to login or dashboard."""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('auth.login'))


@main_bp.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard with statistics."""
    # Get statistics - matching the template expectations
    stats = {
        'total_files': File.query.count(),
        'active_files': File.query.filter(db.or_(File.is_closed == 0, File.is_closed == None)).count(),
        'closed_files': File.query.filter(File.is_closed == 1).count(),
        'pending_files': ReportSoughtDetails.query.filter(
            and_(
                or_(ReportSoughtDetails.submitted != 'Yes', ReportSoughtDetails.submitted == None),
                ReportSoughtDetails.report_sought_date != None,
                ReportSoughtDetails.report_sought_date != ''
            )
        ).count(),
        'physical_files': File.query.filter_by(file_type='Physical').count(),
        'eoffice_files': File.query.filter_by(file_type='E-Office').count(),
        'disciplinary_actions': DisciplinaryAction.query.count(),
        'rti_applications': RTIApplication.query.count(),
        'court_cases': CourtCase.query.count(),
        'employees': Employee.query.count(),
        'institutions': Institution.query.count(),
        'inquiries': InquiryDetails.query.count()
    }
    
    # Get recently updated files - order by last_modified timestamp
    # Use raw SQL with REPLACE to normalize both 'T' and space formats for proper sorting
    recent_files_query = db.session.execute(
        db.text("""
            SELECT file_number FROM files 
            WHERE last_modified IS NOT NULL AND last_modified != ''
            ORDER BY REPLACE(last_modified, 'T', ' ') DESC 
            LIMIT 10
        """)
    ).fetchall()
    recent_file_numbers = [row[0] for row in recent_files_query]
    
    # Fetch the full File objects while maintaining order
    if recent_file_numbers:
        recent_files = []
        for fn in recent_file_numbers:
            file = File.query.filter_by(file_number=fn).first()
            if file:
                recent_files.append(file)
    else:
        recent_files = []
    
    # Get files by status
    files_by_status = db.session.query(
        File.status, func.count(File.file_number)
    ).group_by(File.status).all()
    
    # Get files by type
    files_by_type = db.session.query(
        File.file_type, func.count(File.file_number)
    ).group_by(File.file_type).all()
    
    return render_template('main/dashboard.html', 
                          stats=stats, 
                          recent_files=recent_files,
                          files_by_status=dict(files_by_status),
                          files_by_type=dict(files_by_type))


@main_bp.route('/search')
@login_required
def search():
    """Global search page."""
    query = request.args.get('q', '').strip()
    results = []
    
    if query:
        # Search in files
        files = File.query.filter(
            db.or_(
                File.file_number.ilike(f'%{query}%'),
                File.subject.ilike(f'%{query}%'),
                File.details_of_file.ilike(f'%{query}%'),
                File.institution_name.ilike(f'%{query}%')
            )
        ).limit(50).all()
        
        for f in files:
            results.append({
                'type': 'File',
                'title': f.file_number,
                'description': f.subject or '',
                'url': url_for('files.view_file', file_number=f.file_number)
            })
        
        # Search in employees
        employees = Employee.query.filter(
            db.or_(
                Employee.pen.ilike(f'%{query}%'),
                Employee.name.ilike(f'%{query}%'),
                Employee.institution_name.ilike(f'%{query}%')
            )
        ).limit(20).all()
        
        for e in employees:
            results.append({
                'type': 'Employee',
                'title': f'{e.name} ({e.pen})',
                'description': e.designation or '',
                'url': url_for('employees.view_employee', id=e.id)
            })
        
        # Search in RTI applications
        rti_apps = RTIApplication.query.filter(
            db.or_(
                RTIApplication.original_application_no.ilike(f'%{query}%'),
                RTIApplication.applicant_name.ilike(f'%{query}%'),
                RTIApplication.subject_of_information.ilike(f'%{query}%')
            )
        ).limit(20).all()
        
        for r in rti_apps:
            results.append({
                'type': 'RTI Application',
                'title': r.original_application_no or '',
                'description': r.applicant_name or '',
                'url': url_for('rti.view_rti', id=r.id)
            })
    
    return render_template('main/search.html', query=query, results=results)


@main_bp.route('/about')
@login_required
def about():
    """About page."""
    return render_template('main/about.html')


@main_bp.route('/help')
@login_required
def help_page():
    """Help page."""
    return render_template('main/help.html')


@main_bp.route('/api/stats')
@login_required
def api_stats():
    """API endpoint for dashboard statistics."""
    stats = {
        'total_files': File.query.count(),
        'active_files': File.query.filter_by(is_closed=False).count(),
        'closed_files': File.query.filter_by(is_closed=True).count(),
        'physical_files': File.query.filter_by(file_type='Physical').count(),
        'eoffice_files': File.query.filter_by(file_type='E-Office').count(),
        'disciplinary_actions': DisciplinaryAction.query.count(),
        'rti_applications': RTIApplication.query.count(),
        'court_cases': CourtCase.query.count()
    }
    return jsonify(stats)


@main_bp.route('/admin/fix-sequences')
@login_required
def fix_sequences():
    """Fix PostgreSQL sequences that are out of sync after data import."""
    if not current_user.is_admin():
        flash('Admin access required.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    try:
        # List of tables with auto-increment IDs that need sequence fixing
        tables_to_fix = [
            'report_asked_details',
            'report_sought_details',
            'trace_details',
            'preliminary_statements',
            'rule15_statements',
            'rti_applications',
            'rti_application_details',
            'court_cases',
            'court_case_details',
            'women_harassment_cases',
            'complaint_details',
            'cmo_portal_details',
            'rvu_details',
            'social_security_pension_details',
            'kescpcr_details',
            'khrc_details',
            'scst_details',
            'kwc_details',
            'vigilance_ac_details',
            'rajya_lok_niyamasabha_details',
            'police_case_details',
            'attack_on_doctors_cases',
            'attack_on_staffs_cases',
            'pr_entries',
            'pr_entry_details',
            'inquiry_details',
            'disciplinary_actions',
            'disciplinary_action_details',
            'unauthorised_absentee_details',
            'employees',
            'institutions',
            'file_migrations',
            'communications',
            'communication_details'
        ]
        
        fixed_tables = []
        for table in tables_to_fix:
            try:
                # Reset the sequence to the max ID + 1
                sql = f"""
                    SELECT setval(
                        pg_get_serial_sequence('{table}', 'id'),
                        COALESCE((SELECT MAX(id) FROM {table}), 1),
                        true
                    );
                """
                db.session.execute(db.text(sql))
                fixed_tables.append(table)
            except Exception as e:
                # Skip tables that don't exist or don't have sequences
                pass
        
        db.session.commit()
        flash(f'Successfully fixed sequences for {len(fixed_tables)} tables.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error fixing sequences: {str(e)}', 'danger')
    
    return redirect(url_for('main.dashboard'))


@main_bp.route('/admin/init-categories-and-types')
@login_required
def init_categories_and_types():
    """Initialize categories and file types tables with default values."""
    if not current_user.is_admin():
        flash('Admin access required.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    try:
        from models import FileType, Category
        
        # Default file types
        default_file_types = [
            "Women Harassment", "Police Case", "Medical Negligence",
            "Attack on Doctors", "Attack on Staffs", "Unauthorised Absence",
            "RTI", "Duty Lapse", "Private Practice", "Denial of Treatment",
            "Social Security Pension", "Others"
        ]
        
        # Default categories
        default_categories = [
            "CMO Portal", "RVU", "KeSCPCR", "KHRC", "NKS",
            "SC/ST", "KWC", "Court Case", "Rajya/Lok/Niyamasabha",
            "Vig & Anti Corruption", "Complaint", "Others"
        ]
        
        added_types = 0
        added_cats = 0
        
        # Add file types if they don't exist
        for ft_name in default_file_types:
            if not FileType.query.filter_by(name=ft_name).first():
                ft = FileType(name=ft_name)
                db.session.add(ft)
                added_types += 1
        
        # Add categories if they don't exist
        for cat_name in default_categories:
            if not Category.query.filter_by(name=cat_name).first():
                cat = Category(name=cat_name)
                db.session.add(cat)
                added_cats += 1
        
        db.session.commit()
        flash(f'Successfully initialized! Added {added_types} file types and {added_cats} categories.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error initializing: {str(e)}', 'danger')
    
    return redirect(url_for('main.dashboard'))
