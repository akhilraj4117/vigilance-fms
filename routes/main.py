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
