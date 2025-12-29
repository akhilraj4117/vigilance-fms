"""
Employee management routes for the Flask application.
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, Response
from flask_login import login_required, current_user
from models import Employee, Institution, DisciplinaryAction
from extensions import db
from utils import convert_date_format
from sqlalchemy import or_
import csv
import io

employees_bp = Blueprint('employees', __name__)


@employees_bp.route('/')
@login_required
def list_employees():
    """List all employees."""
    page = request.args.get('page', 1, type=int)
    per_page = 25
    
    # Get filter parameters
    search_query = request.args.get('q', '').strip()
    institution_filter = request.args.get('institution', '')
    designation_filter = request.args.get('designation', '')
    sort_by = request.args.get('sort', '')
    sort_order = request.args.get('order', 'asc')
    
    query = Employee.query
    
    if search_query:
        query = query.filter(
            or_(
                Employee.name.ilike(f'%{search_query}%'),
                Employee.pen.ilike(f'%{search_query}%'),
                Employee.designation.ilike(f'%{search_query}%'),
                Employee.institution_name.ilike(f'%{search_query}%')
            )
        )
    
    if institution_filter:
        query = query.filter(Employee.institution_name == institution_filter)
    
    if designation_filter:
        query = query.filter(Employee.designation == designation_filter)
    
    # Apply sorting
    if sort_by:
        sort_column = None
        if sort_by == 'name':
            sort_column = Employee.name
        elif sort_by == 'pen':
            sort_column = Employee.pen
        elif sort_by == 'designation':
            sort_column = Employee.designation
        elif sort_by == 'institution_name':
            sort_column = Employee.institution_name
        elif sort_by == 'joining_date':
            sort_column = Employee.joining_date
        
        if sort_column is not None:
            if sort_order == 'desc':
                query = query.order_by(sort_column.desc())
            else:
                query = query.order_by(sort_column.asc())
        else:
            query = query.order_by(Employee.name.asc())
    else:
        query = query.order_by(Employee.name.asc())
    
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    employees = pagination.items
    
    # Get unique institutions and designations for filter dropdowns
    institutions = db.session.query(Employee.institution_name).distinct().filter(
        Employee.institution_name != None, Employee.institution_name != ''
    ).order_by(Employee.institution_name.asc()).all()
    institutions = [i[0] for i in institutions]
    
    designations = db.session.query(Employee.designation).distinct().filter(
        Employee.designation != None, Employee.designation != ''
    ).order_by(Employee.designation.asc()).all()
    designations = [d[0] for d in designations]
    
    return render_template('employees/list.html', 
                          employees=employees, 
                          pagination=pagination,
                          search_query=search_query,
                          institution_filter=institution_filter,
                          designation_filter=designation_filter,
                          institutions=institutions,
                          designations=designations,
                          sort_by=sort_by,
                          sort_order=sort_order)


@employees_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_employee():
    """Create a new employee."""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        pen = request.form.get('pen', '').strip()
        
        if not name:
            flash('Employee name is required.', 'danger')
            return render_template('employees/create.html')
        
        # Check for duplicate PEN if provided
        if pen:
            existing = Employee.query.filter_by(pen=pen).first()
            if existing:
                flash(f'Employee with PEN {pen} already exists.', 'danger')
                return render_template('employees/create.html')
        
        employee = Employee(
            name=name,
            pen=pen,
            designation=request.form.get('designation', ''),
            institution_name=request.form.get('institution_name', ''),
            date_of_birth=convert_date_format(request.form.get('date_of_birth', '')),
            joining_date=convert_date_format(request.form.get('joining_date', '')),
            permanent_address=request.form.get('permanent_address', ''),
            communication_address=request.form.get('communication_address', '')
        )
        
        db.session.add(employee)
        db.session.commit()
        
        flash('Employee created successfully.', 'success')
        return redirect(url_for('employees.view_employee', id=employee.id))
    
    # Get all institutions for dropdown
    institutions = Institution.query.order_by(Institution.name.asc()).all()
    
    return render_template('employees/create.html', institutions=institutions)


@employees_bp.route('/<int:id>')
@login_required
def view_employee(id):
    """View employee details."""
    employee = Employee.query.get_or_404(id)
    
    # Get disciplinary actions for this employee
    da_records = DisciplinaryAction.query.filter_by(pen=employee.pen).all() if employee.pen else []
    
    return render_template('employees/view.html', 
                          employee=employee, 
                          da_records=da_records)


@employees_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_employee(id):
    """Edit employee."""
    employee = Employee.query.get_or_404(id)
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        
        if not name:
            flash('Employee name is required.', 'danger')
            institutions = Institution.query.order_by(Institution.name.asc()).all()
            return render_template('employees/edit.html', employee=employee, institutions=institutions)
        
        # Check for duplicate PEN if changed
        new_pen = request.form.get('pen', '').strip()
        if new_pen and new_pen != employee.pen:
            existing = Employee.query.filter_by(pen=new_pen).first()
            if existing:
                flash(f'Employee with PEN {new_pen} already exists.', 'danger')
                institutions = Institution.query.order_by(Institution.name.asc()).all()
                return render_template('employees/edit.html', employee=employee, institutions=institutions)
        
        # Update disciplinary actions if PEN changed
        old_pen = employee.pen
        
        employee.name = name
        employee.pen = new_pen
        employee.designation = request.form.get('designation', '')
        employee.institution_name = request.form.get('institution_name', '')
        employee.date_of_birth = convert_date_format(request.form.get('date_of_birth', ''))
        employee.joining_date = convert_date_format(request.form.get('joining_date', ''))
        employee.permanent_address = request.form.get('permanent_address', '')
        employee.communication_address = request.form.get('communication_address', '')
        
        # Update disciplinary actions if PEN changed
        if old_pen and new_pen and old_pen != new_pen:
            da_records = DisciplinaryAction.query.filter_by(pen=old_pen).all()
            for da in da_records:
                da.pen = new_pen
        
        db.session.commit()
        
        flash('Employee updated successfully.', 'success')
        return redirect(url_for('employees.view_employee', id=id))
    
    # Get all institutions for dropdown
    institutions = Institution.query.order_by(Institution.name.asc()).all()
    
    return render_template('employees/edit.html', employee=employee, institutions=institutions)


@employees_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete_employee(id):
    """Delete employee."""
    if not current_user.is_admin():
        flash('Only administrators can delete employees.', 'danger')
        return redirect(url_for('employees.view_employee', id=id))
    
    employee = Employee.query.get_or_404(id)
    
    # Check if there are disciplinary actions for this employee
    if employee.pen:
        da_count = DisciplinaryAction.query.filter_by(pen=employee.pen).count()
        if da_count > 0:
            flash(f'Cannot delete employee. {da_count} disciplinary actions are linked to this PEN.', 'danger')
            return redirect(url_for('employees.view_employee', id=id))
    
    db.session.delete(employee)
    db.session.commit()
    
    flash('Employee deleted successfully.', 'success')
    return redirect(url_for('employees.list_employees'))


@employees_bp.route('/api/search')
@login_required
def api_search_employees():
    """API endpoint for searching employees (for autocomplete)."""
    query = request.args.get('q', '').strip()
    limit = request.args.get('limit', 10, type=int)
    
    if not query or len(query) < 2:
        return jsonify([])
    
    employees = Employee.query.filter(
        or_(
            Employee.name.ilike(f'%{query}%'),
            Employee.pen.ilike(f'%{query}%')
        )
    ).limit(limit).all()
    
    results = [{
        'id': emp.id,
        'name': emp.name,
        'pen': emp.pen,
        'designation': emp.designation,
        'institution': emp.institution_name
    } for emp in employees]
    
    return jsonify(results)


@employees_bp.route('/api/save', methods=['POST'])
@login_required
def save_employee_ajax():
    """AJAX endpoint for saving/updating employee (matching desktop app behavior)."""
    try:
        data = request.get_json()
        
        pen = data.get('pen', '').strip()
        name = data.get('name', '').strip()
        
        if not pen:
            return jsonify({'success': False, 'message': 'PEN is required to save employee details.'})
        
        # Check if employee exists (by PEN for update, not by edit_id)
        existing = Employee.query.filter_by(pen=pen).first()
        
        if existing:
            # Update existing employee
            existing.name = name
            existing.designation = data.get('designation', '')
            existing.institution_name = data.get('institution_name', '')
            existing.date_of_birth = data.get('date_of_birth', '')
            existing.joining_date = data.get('joining_date', '')
            existing.permanent_address = data.get('permanent_address', '')
            existing.communication_address = data.get('communication_address', '')
            
            db.session.commit()
            return jsonify({'success': True, 'message': 'Employee details updated successfully!'})
        else:
            # Create new employee
            employee = Employee(
                pen=pen,
                name=name,
                designation=data.get('designation', ''),
                institution_name=data.get('institution_name', ''),
                date_of_birth=data.get('date_of_birth', ''),
                joining_date=data.get('joining_date', ''),
                permanent_address=data.get('permanent_address', ''),
                communication_address=data.get('communication_address', '')
            )
            
            db.session.add(employee)
            db.session.commit()
            return jsonify({'success': True, 'message': 'Employee details saved successfully!'})
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})


@employees_bp.route('/api/get/<pen>')
@login_required
def api_get_employee(pen):
    """API endpoint to get employee details by PEN."""
    employee = Employee.query.filter_by(pen=pen).first()
    
    if employee:
        return jsonify({
            'found': True,
            'id': employee.id,
            'name': employee.name,
            'pen': employee.pen,
            'designation': employee.designation,
            'institution_name': employee.institution_name,
            'joining_date': employee.joining_date,
            'date_of_birth': employee.date_of_birth
        })
    else:
        return jsonify({'found': False})


@employees_bp.route('/export')
@login_required
def export_employees():
    """Export employees to CSV."""
    employees = Employee.query.order_by(Employee.name.asc()).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Add UTF-8 BOM for Excel to recognize Unicode characters (Malayalam etc.)
    output.write('\ufeff')
    
    # Write header
    writer.writerow([
        'PEN', 'Name', 'Designation', 'Institution', 
        'Date of Birth', 'Joining Date',
        'Permanent Address', 'Communication Address'
    ])
    
    # Write data
    for emp in employees:
        writer.writerow([
            emp.pen,
            emp.name,
            emp.designation,
            emp.institution_name,
            emp.date_of_birth,
            emp.joining_date,
            emp.permanent_address,
            emp.communication_address
        ])
    
    output.seek(0)
    
    return Response(
        output.getvalue().encode('utf-8-sig'),
        mimetype='text/csv; charset=utf-8-sig',
        headers={'Content-Disposition': 'attachment; filename=employees.csv'}
    )


@employees_bp.route('/import', methods=['GET', 'POST'])
@login_required
def import_employees():
    """Import employees from CSV."""
    if not current_user.is_admin():
        flash('Only administrators can import employees.', 'danger')
        return redirect(url_for('employees.list_employees'))
    
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file uploaded.', 'danger')
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            flash('No file selected.', 'danger')
            return redirect(request.url)
        
        if not file.filename.endswith('.csv'):
            flash('Please upload a CSV file.', 'danger')
            return redirect(request.url)
        
        try:
            stream = io.StringIO(file.stream.read().decode('utf-8'))
            reader = csv.DictReader(stream)
            
            count = 0
            errors = []
            
            for row in reader:
                pen = row.get('pen', '').strip() or row.get('PEN', '').strip()
                name = row.get('name', '').strip() or row.get('Name', '').strip()
                
                if not name:
                    continue
                
                # Check if PEN already exists
                if pen:
                    existing = Employee.query.filter_by(pen=pen).first()
                    if existing:
                        errors.append(f"Employee with PEN '{pen}' already exists")
                        continue
                
                employee = Employee(
                    pen=pen,
                    name=name,
                    designation=row.get('designation', '') or row.get('Designation', ''),
                    institution_name=row.get('institution_name', '') or row.get('Institution', ''),
                    date_of_birth=convert_date_format(row.get('date_of_birth', '') or row.get('Date of Birth', '')),
                    joining_date=convert_date_format(row.get('joining_date', '') or row.get('Joining Date', '')),
                    permanent_address=row.get('permanent_address', '') or row.get('Permanent Address', ''),
                    communication_address=row.get('communication_address', '') or row.get('Communication Address', '')
                )
                
                db.session.add(employee)
                count += 1
            
            db.session.commit()
            
            if errors:
                flash(f'Imported {count} employees. Errors: {len(errors)}', 'warning')
            else:
                flash(f'Successfully imported {count} employees.', 'success')
            
            return redirect(url_for('employees.list_employees'))
            
        except Exception as e:
            flash(f'Error importing file: {str(e)}', 'danger')
            return redirect(request.url)
    
    return render_template('employees/import.html')


@employees_bp.route('/by-institution/<institution_name>')
@login_required
def by_institution(institution_name):
    """List employees by institution."""
    page = request.args.get('page', 1, type=int)
    per_page = 25
    
    query = Employee.query.filter_by(institution_name=institution_name)
    query = query.order_by(Employee.name.asc())
    
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    employees = pagination.items
    
    return render_template('employees/by_institution.html', 
                          employees=employees, 
                          pagination=pagination,
                          institution_name=institution_name)
