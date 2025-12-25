"""
Institution management routes for the Flask application.
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, Response
from flask_login import login_required, current_user
from models import Institution, Employee, InstitutionCategory
from extensions import db
from sqlalchemy import or_
import csv
import io

institutions_bp = Blueprint('institutions', __name__)


@institutions_bp.route('/')
@login_required
def list_institutions():
    """List all institutions."""
    page = request.args.get('page', 1, type=int)
    per_page = 25
    
    # Get filter parameters
    search_query = request.args.get('q', '').strip()
    institution_type = request.args.get('type', '')
    
    query = Institution.query
    
    if search_query:
        query = query.filter(
            or_(
                Institution.name.ilike(f'%{search_query}%'),
                Institution.category.ilike(f'%{search_query}%'),
                Institution.address.ilike(f'%{search_query}%'),
                Institution.head_name.ilike(f'%{search_query}%')
            )
        )
    
    if institution_type:
        query = query.filter(Institution.category == institution_type)
    
    # Order by name
    query = query.order_by(Institution.name.asc())
    
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    institutions = pagination.items
    
    # Get unique types for filter dropdown
    types = db.session.query(Institution.category).distinct().filter(Institution.category != None, Institution.category != '').all()
    types = [t[0] for t in types]
    
    return render_template('institutions/list.html', 
                          institutions=institutions, 
                          pagination=pagination,
                          search_query=search_query,
                          institution_type=institution_type,
                          types=types)


def get_all_categories():
    """Get all categories from both InstitutionCategory table and distinct categories used by institutions."""
    # Get categories from the categories table
    db_categories = [cat.name for cat in InstitutionCategory.query.order_by(InstitutionCategory.name.asc()).all()]
    
    # Get distinct categories already used by institutions
    used_categories = db.session.query(Institution.category).distinct().filter(
        Institution.category != None, 
        Institution.category != ''
    ).all()
    used_categories = [c[0] for c in used_categories]
    
    # Merge and deduplicate, maintaining a sensible order
    all_categories = list(set(db_categories + used_categories))
    all_categories.sort()
    
    return all_categories


@institutions_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_institution():
    """Create a new institution."""
    # Get categories for dropdown (from both DB table and used categories)
    categories = get_all_categories()
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        
        if not name:
            flash('Institution name is required.', 'danger')
            return render_template('institutions/create.html', categories=categories)
        
        # Check for duplicate name
        existing = Institution.query.filter_by(name=name).first()
        if existing:
            flash('Institution with this name already exists.', 'danger')
            return render_template('institutions/create.html', categories=categories)
        
        # Get staff details (from hidden JSON field)
        staff_details = request.form.get('staff_details', '[]')
        
        institution = Institution(
            name=name,
            category=request.form.get('category', ''),
            address=request.form.get('address', ''),
            contact_number=request.form.get('contact_number', ''),
            email=request.form.get('email', ''),
            head_of_institution=request.form.get('head_of_institution', ''),
            head_name=request.form.get('head_name', ''),
            head_contact=request.form.get('head_contact', ''),
            staff_details=staff_details
        )
        
        db.session.add(institution)
        db.session.commit()
        
        flash('Institution created successfully.', 'success')
        return redirect(url_for('institutions.view_institution', id=institution.id))
    
    return render_template('institutions/create.html', categories=categories)


@institutions_bp.route('/<int:id>')
@login_required
def view_institution(id):
    """View institution details."""
    institution = Institution.query.get_or_404(id)
    
    # Get employees in this institution
    employees = Employee.query.filter_by(institution_name=institution.name).all()
    
    return render_template('institutions/view.html', 
                          institution=institution, 
                          employees=employees)


@institutions_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_institution(id):
    """Edit institution."""
    institution = Institution.query.get_or_404(id)
    
    # Get categories for dropdown (from both DB table and used categories)
    categories = get_all_categories()
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        
        if not name:
            flash('Institution name is required.', 'danger')
            return render_template('institutions/edit.html', institution=institution, categories=categories)
        
        # Update fields
        old_name = institution.name
        institution.name = name
        institution.category = request.form.get('category', '')
        institution.address = request.form.get('address', '')
        institution.contact_number = request.form.get('contact_number', '')
        institution.email = request.form.get('email', '')
        institution.head_of_institution = request.form.get('head_of_institution', '')
        institution.head_name = request.form.get('head_name', '')
        institution.head_contact = request.form.get('head_contact', '')
        
        # Get staff details (from hidden JSON field)
        institution.staff_details = request.form.get('staff_details', '[]')
        
        # Update employees if institution name changed
        if old_name != name:
            employees = Employee.query.filter_by(institution_name=old_name).all()
            for emp in employees:
                emp.institution_name = name
        
        db.session.commit()
        
        flash('Institution updated successfully.', 'success')
        return redirect(url_for('institutions.view_institution', id=id))
    
    return render_template('institutions/edit.html', institution=institution, categories=categories)


@institutions_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete_institution(id):
    """Delete institution."""
    if not current_user.is_admin():
        flash('Only administrators can delete institutions.', 'danger')
        return redirect(url_for('institutions.view_institution', id=id))
    
    institution = Institution.query.get_or_404(id)
    
    # Check if there are employees in this institution
    employee_count = Employee.query.filter_by(institution_name=institution.name).count()
    if employee_count > 0:
        flash(f'Cannot delete institution. {employee_count} employees are assigned to it.', 'danger')
        return redirect(url_for('institutions.view_institution', id=id))
    
    db.session.delete(institution)
    db.session.commit()
    
    flash('Institution deleted successfully.', 'success')
    return redirect(url_for('institutions.list_institutions'))


@institutions_bp.route('/api/search')
@login_required
def api_search_institutions():
    """API endpoint for searching institutions (for autocomplete)."""
    query = request.args.get('q', '').strip()
    limit = request.args.get('limit', 10, type=int)
    
    if not query or len(query) < 2:
        return jsonify([])
    
    institutions = Institution.query.filter(
        or_(
            Institution.name.ilike(f'%{query}%'),
            Institution.category.ilike(f'%{query}%')
        )
    ).limit(limit).all()
    
    results = [{
        'id': inst.id,
        'name': inst.name,
        'category': inst.category,
        'head_name': inst.head_name
    } for inst in institutions]
    
    return jsonify(results)


@institutions_bp.route('/api/list')
@login_required
def api_list_institutions():
    """API endpoint to get all institution names."""
    institutions = Institution.query.order_by(Institution.name.asc()).all()
    return jsonify([{'id': inst.id, 'name': inst.name} for inst in institutions])


@institutions_bp.route('/types')
@login_required
def list_types():
    """List institutions grouped by category."""
    types = db.session.query(Institution.category, db.func.count(Institution.id)).group_by(Institution.category).all()
    
    type_data = []
    for inst_type, count in types:
        if inst_type:
            type_data.append({
                'type': inst_type,
                'count': count
            })
    
    return render_template('institutions/types.html', type_data=type_data)


@institutions_bp.route('/import', methods=['GET', 'POST'])
@login_required
def import_institutions():
    """Import institutions from CSV or Excel file."""
    if not current_user.is_admin():
        flash('Only administrators can import institutions.', 'danger')
        return redirect(url_for('institutions.list_institutions'))
    
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file uploaded.', 'danger')
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            flash('No file selected.', 'danger')
            return redirect(request.url)
        
        filename = file.filename.lower()
        if not (filename.endswith('.csv') or filename.endswith('.xlsx') or filename.endswith('.xls')):
            flash('Please upload a CSV or Excel file (.csv, .xlsx, .xls).', 'danger')
            return redirect(request.url)
        
        try:
            count = 0
            errors = []
            
            if filename.endswith('.csv'):
                # Handle CSV file
                stream = io.StringIO(file.stream.read().decode('utf-8'))
                reader = csv.DictReader(stream)
                rows = list(reader)
            else:
                # Handle Excel file
                import pandas as pd
                df = pd.read_excel(file)
                rows = df.to_dict('records')
            
            for row in rows:
                # Get name from various possible column names
                name = str(row.get('Name of Institution', '') or row.get('name', '') or row.get('Name', '')).strip()
                if not name:
                    continue
                
                # Check if already exists
                existing = Institution.query.filter_by(name=name).first()
                if existing:
                    errors.append(f"Institution '{name}' already exists")
                    continue
                
                institution = Institution(
                    name=name,
                    category=str(row.get('Category', '') or row.get('category', '')).strip(),
                    address=str(row.get('Address', '') or row.get('address', '')).strip(),
                    contact_number=str(row.get('Contact Number', '') or row.get('contact_number', '')).strip(),
                    email=str(row.get('E-mail', '') or row.get('email', '') or row.get('Email', '')).strip(),
                    head_of_institution=str(row.get('Head of Institution', '') or row.get('head_of_institution', '')).strip(),
                    head_name=str(row.get('Name of Head', '') or row.get('head_name', '') or row.get('Head Name', '')).strip(),
                    head_contact=str(row.get('Contact Number of Head', '') or row.get('head_contact', '') or row.get('Head Contact', '')).strip(),
                    staff_details=str(row.get('Staff Details', '') or row.get('staff_details', '')).strip()
                )
                
                db.session.add(institution)
                count += 1
            
            db.session.commit()
            
            if errors:
                flash(f'Imported {count} institutions. Skipped {len(errors)} existing institutions.', 'warning')
            else:
                flash(f'Successfully imported {count} institutions.', 'success')
            
            return redirect(url_for('institutions.list_institutions'))
            
        except Exception as e:
            flash(f'Error importing file: {str(e)}', 'danger')
            return redirect(request.url)
    
    return render_template('institutions/import.html')


@institutions_bp.route('/export')
@login_required
def export_institutions():
    """Export all institutions to CSV (Excel compatible)."""
    institutions = Institution.query.order_by(Institution.name.asc()).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Add UTF-8 BOM for Excel to recognize Unicode characters (Malayalam etc.)
    output.write('\ufeff')
    
    # Write header matching desktop app export format
    writer.writerow([
        'Sl. No.', 'Name of Institution', 'Category', 'Address', 
        'Contact Number', 'E-mail', 'Head of Institution', 
        'Name of Head', 'Contact Number of Head', 'Staff Details'
    ])
    
    # Write data
    for i, inst in enumerate(institutions, 1):
        writer.writerow([
            i,
            inst.name or '',
            inst.category or '',
            inst.address or '',
            inst.contact_number or '',
            inst.email or '',
            inst.head_of_institution or '',
            inst.head_name or '',
            inst.head_contact or '',
            inst.staff_details or ''
        ])
    
    output.seek(0)
    
    return Response(
        output.getvalue().encode('utf-8-sig'),
        mimetype='text/csv; charset=utf-8-sig',
        headers={'Content-Disposition': 'attachment; filename=institutions.csv'}
    )


@institutions_bp.route('/categories')
@login_required
def manage_categories():
    """Manage institution categories."""
    categories = InstitutionCategory.query.order_by(InstitutionCategory.name.asc()).all()
    
    # Get all category names from the table
    db_category_names = set(cat.name for cat in categories)
    
    # Count institutions per category from table
    category_data = []
    for cat in categories:
        count = Institution.query.filter_by(category=cat.name).count()
        category_data.append({
            'id': cat.id,
            'name': cat.name,
            'count': count,
            'in_table': True
        })
    
    # Also get categories used by institutions but NOT in the categories table
    used_categories = db.session.query(Institution.category, db.func.count(Institution.id)).filter(
        Institution.category != None, 
        Institution.category != ''
    ).group_by(Institution.category).all()
    
    for cat_name, count in used_categories:
        if cat_name not in db_category_names:
            category_data.append({
                'id': None,  # No ID since it's not in the categories table
                'name': cat_name,
                'count': count,
                'in_table': False
            })
    
    # Sort by name
    category_data.sort(key=lambda x: x['name'])
    
    return render_template('institutions/categories.html', categories=category_data)


@institutions_bp.route('/categories/add', methods=['POST'])
@login_required
def add_category():
    """Add a new institution category."""
    name = request.form.get('name', '').strip()
    
    if not name:
        flash('Category name is required.', 'danger')
        return redirect(url_for('institutions.manage_categories'))
    
    # Check for duplicate
    existing = InstitutionCategory.query.filter_by(name=name).first()
    if existing:
        flash('Category with this name already exists.', 'danger')
        return redirect(url_for('institutions.manage_categories'))
    
    category = InstitutionCategory(name=name)
    db.session.add(category)
    db.session.commit()
    
    flash(f'Category "{name}" added successfully.', 'success')
    return redirect(url_for('institutions.manage_categories'))


@institutions_bp.route('/categories/<int:id>/edit', methods=['POST'])
@login_required
def edit_category(id):
    """Edit an institution category."""
    category = InstitutionCategory.query.get_or_404(id)
    old_name = category.name
    new_name = request.form.get('name', '').strip()
    
    if not new_name:
        flash('Category name is required.', 'danger')
        return redirect(url_for('institutions.manage_categories'))
    
    # Check for duplicate
    existing = InstitutionCategory.query.filter(
        InstitutionCategory.name == new_name,
        InstitutionCategory.id != id
    ).first()
    if existing:
        flash('Category with this name already exists.', 'danger')
        return redirect(url_for('institutions.manage_categories'))
    
    # Update the category name
    category.name = new_name
    
    # Update institutions that use this category
    if old_name != new_name:
        institutions = Institution.query.filter_by(category=old_name).all()
        for inst in institutions:
            inst.category = new_name
    
    db.session.commit()
    
    flash(f'Category renamed from "{old_name}" to "{new_name}".', 'success')
    return redirect(url_for('institutions.manage_categories'))


@institutions_bp.route('/categories/<int:id>/delete', methods=['POST'])
@login_required
def delete_category(id):
    """Delete an institution category."""
    if not current_user.is_admin():
        flash('Only administrators can delete categories.', 'danger')
        return redirect(url_for('institutions.manage_categories'))
    
    category = InstitutionCategory.query.get_or_404(id)
    
    # Check if any institutions use this category
    count = Institution.query.filter_by(category=category.name).count()
    if count > 0:
        flash(f'Cannot delete category "{category.name}". {count} institutions are using it.', 'danger')
        return redirect(url_for('institutions.manage_categories'))
    
    db.session.delete(category)
    db.session.commit()
    
    flash(f'Category "{category.name}" deleted successfully.', 'success')
    return redirect(url_for('institutions.manage_categories'))