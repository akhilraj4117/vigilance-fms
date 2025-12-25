"""
API routes for the Flask application.
External API endpoints for integration with other systems.
"""
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from models import (
    File, DisciplinaryAction, RTIApplication, Employee, Institution,
    CourtCase, InquiryDetails, WomenHarassmentCase, SocialSecurityPension
)
from extensions import db
from sqlalchemy import or_, func
from functools import wraps

api_bp = Blueprint('api', __name__)


def api_key_required(f):
    """Decorator to require API key for endpoints."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        # For now, we'll skip API key validation and use login_required
        # In production, implement proper API key validation
        if not current_user.is_authenticated:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function


@api_bp.route('/health')
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'message': 'Vigilance File Management System API is running'
    })


@api_bp.route('/stats')
@login_required
def get_stats():
    """Get overall statistics."""
    stats = {
        'files': {
            'total': File.query.count(),
            'pending': File.query.filter(or_(File.status == 'Pending', File.status == 'Open')).count(),
            'closed': File.query.filter(File.status == 'Closed').count()
        },
        'disciplinary_actions': {
            'total': DisciplinaryAction.query.count(),
            'pending': DisciplinaryAction.query.filter(
                or_(DisciplinaryAction.finalised_date == None, DisciplinaryAction.finalised_date == '')
            ).count()
        },
        'rti_applications': {
            'total': RTIApplication.query.count(),
            'pending': RTIApplication.query.filter(RTIApplication.status != 'Disposed').count()
        },
        'employees': Employee.query.count(),
        'institutions': Institution.query.count(),
        'court_cases': CourtCase.query.count(),
        'inquiries': InquiryDetails.query.count()
    }
    
    return jsonify(stats)


@api_bp.route('/files')
@login_required
def list_files():
    """List files with pagination."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    search = request.args.get('q', '')
    category = request.args.get('category', '')
    status = request.args.get('status', '')
    
    query = File.query
    
    if search:
        query = query.filter(
            or_(
                File.file_number.ilike(f'%{search}%'),
                File.subject.ilike(f'%{search}%')
            )
        )
    
    if category:
        query = query.filter(File.category == category)
    
    if status:
        query = query.filter(File.status == status)
    
    pagination = query.order_by(File.file_number.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    files = [{
        'file_number': f.file_number,
        'category': f.category,
        'subject': f.subject,
        'status': f.status,
        'date_of_receipt': f.date_of_receipt,
        'from_whom_received': f.from_whom_received
    } for f in pagination.items]
    
    return jsonify({
        'files': files,
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page,
        'has_next': pagination.has_next,
        'has_prev': pagination.has_prev
    })


@api_bp.route('/files/<file_number>')
@login_required
def get_file(file_number):
    """Get file details."""
    file = File.query.filter_by(file_number=file_number).first()
    
    if not file:
        return jsonify({'error': 'File not found'}), 404
    
    return jsonify({
        'file_number': file.file_number,
        'category': file.category,
        'file_type': file.file_type,
        'subject': file.subject,
        'from_whom_received': file.from_whom_received,
        'date_of_receipt': file.date_of_receipt,
        'status': file.status,
        'file_closed_date': file.file_closed_date,
        'closing_remarks': file.closing_remarks,
        'last_modified': file.last_modified
    })


@api_bp.route('/disciplinary-actions')
@login_required
def list_disciplinary_actions():
    """List disciplinary actions."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    search = request.args.get('q', '')
    
    query = DisciplinaryAction.query
    
    if search:
        query = query.filter(
            or_(
                DisciplinaryAction.file_number.ilike(f'%{search}%'),
                DisciplinaryAction.pen.ilike(f'%{search}%'),
                DisciplinaryAction.employee_name.ilike(f'%{search}%')
            )
        )
    
    pagination = query.order_by(DisciplinaryAction.id.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    actions = [{
        'id': da.id,
        'file_number': da.file_number,
        'pen': da.pen,
        'employee_name': da.employee_name,
        'institution': da.institution,
        'major_minor': da.major_minor,
        'finalised_date': da.finalised_date
    } for da in pagination.items]
    
    return jsonify({
        'disciplinary_actions': actions,
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    })


@api_bp.route('/rti-applications')
@login_required
def list_rti_applications():
    """List RTI applications."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    status = request.args.get('status', '')
    
    query = RTIApplication.query
    
    if status:
        query = query.filter(RTIApplication.status == status)
    
    pagination = query.order_by(RTIApplication.id.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    applications = [{
        'id': app.id,
        'file_number': app.file_number,
        'applicant_name': app.applicant_name,
        'subject': app.subject,
        'application_date': app.application_date,
        'status': app.status,
        'appeal_status': app.appeal_status
    } for app in pagination.items]
    
    return jsonify({
        'rti_applications': applications,
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    })


@api_bp.route('/employees')
@login_required
def list_employees():
    """List employees."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    search = request.args.get('q', '')
    institution = request.args.get('institution', '')
    
    query = Employee.query
    
    if search:
        query = query.filter(
            or_(
                Employee.name.ilike(f'%{search}%'),
                Employee.pen.ilike(f'%{search}%')
            )
        )
    
    if institution:
        query = query.filter(Employee.institution_name == institution)
    
    pagination = query.order_by(Employee.name.asc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    employees = [{
        'id': emp.id,
        'name': emp.name,
        'pen': emp.pen,
        'designation': emp.designation,
        'institution_name': emp.institution_name
    } for emp in pagination.items]
    
    return jsonify({
        'employees': employees,
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    })


@api_bp.route('/employees/<pen>')
@login_required
def get_employee(pen):
    """Get employee by PEN."""
    employee = Employee.query.filter_by(pen=pen).first()
    
    if not employee:
        return jsonify({'error': 'Employee not found'}), 404
    
    return jsonify({
        'id': employee.id,
        'name': employee.name,
        'pen': employee.pen,
        'designation': employee.designation,
        'institution_name': employee.institution_name,
        'date_of_birth': employee.date_of_birth,
        'joining_date': employee.joining_date
    })


@api_bp.route('/institutions')
@login_required
def list_institutions():
    """List institutions."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    search = request.args.get('q', '')
    
    query = Institution.query
    
    if search:
        query = query.filter(
            or_(
                Institution.name.ilike(f'%{search}%'),
                Institution.category.ilike(f'%{search}%')
            )
        )
    
    pagination = query.order_by(Institution.name.asc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    institutions = [{
        'id': inst.id,
        'name': inst.name,
        'category': inst.category,
        'head_name': inst.head_name
    } for inst in pagination.items]
    
    return jsonify({
        'institutions': institutions,
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    })


@api_bp.route('/search')
@login_required
def global_search():
    """Global search across all entities."""
    query = request.args.get('q', '').strip()
    limit = request.args.get('limit', 10, type=int)
    
    if not query or len(query) < 2:
        return jsonify({'error': 'Query must be at least 2 characters'}), 400
    
    results = {
        'files': [],
        'employees': [],
        'disciplinary_actions': [],
        'rti_applications': []
    }
    
    # Search files
    files = File.query.filter(
        or_(
            File.file_number.ilike(f'%{query}%'),
            File.subject.ilike(f'%{query}%')
        )
    ).limit(limit).all()
    results['files'] = [{'file_number': f.file_number, 'subject': f.subject} for f in files]
    
    # Search employees
    employees = Employee.query.filter(
        or_(
            Employee.name.ilike(f'%{query}%'),
            Employee.pen.ilike(f'%{query}%')
        )
    ).limit(limit).all()
    results['employees'] = [{'name': e.name, 'pen': e.pen} for e in employees]
    
    # Search disciplinary actions
    das = DisciplinaryAction.query.filter(
        or_(
            DisciplinaryAction.employee_name.ilike(f'%{query}%'),
            DisciplinaryAction.pen.ilike(f'%{query}%')
        )
    ).limit(limit).all()
    results['disciplinary_actions'] = [{'id': da.id, 'employee_name': da.employee_name, 'pen': da.pen} for da in das]
    
    # Search RTI applications
    rtis = RTIApplication.query.filter(
        or_(
            RTIApplication.applicant_name.ilike(f'%{query}%'),
            RTIApplication.subject.ilike(f'%{query}%')
        )
    ).limit(limit).all()
    results['rti_applications'] = [{'id': r.id, 'applicant_name': r.applicant_name, 'subject': r.subject} for r in rtis]
    
    return jsonify(results)


@api_bp.route('/categories')
@login_required
def list_categories():
    """List all file categories."""
    categories = db.session.query(File.category, func.count(File.file_number)).group_by(File.category).all()
    
    return jsonify([{
        'category': cat,
        'count': count
    } for cat, count in categories if cat])


@api_bp.route('/file-types')
@login_required
def list_file_types():
    """List all file types."""
    file_types = db.session.query(File.file_type, func.count(File.file_number)).group_by(File.file_type).all()
    
    return jsonify([{
        'file_type': ft,
        'count': count
    } for ft, count in file_types if ft])
