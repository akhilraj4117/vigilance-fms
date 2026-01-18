"""
Routes for Committee Management (POSH, Disciplinary Action, Suspension Review).
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import db, Committee, CommitteeMember
from datetime import datetime, timedelta
from functools import wraps

committees_bp = Blueprint('committees', __name__, url_prefix='/committees')


def admin_required(f):
    """Decorator to require admin role."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            flash('Admin access required.', 'danger')
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated_function


# Committee type constants
COMMITTEE_TYPES = {
    'POSH': 'Internal Complaints Committee (POSH)',
    'DISC_ACTION': 'Internal Complaints Committee (Disc. Action)',
    'SUSPENSION_REVIEW': 'Suspension Review Committee'
}

# POSH Act Information
POSH_INFO = {
    'act_name': 'Sexual Harassment of Women at Workplace (Prevention, Prohibition and Redressal) Act, 2013',
    'short_name': 'POSH Act, 2013',
    'purpose': '''The POSH Act mandates every employer to constitute an Internal Complaints Committee (ICC) 
                  at every office or branch with 10 or more employees for redressal of complaints of sexual harassment.''',
    'committee_requirements': [
        'Presiding Officer - A senior woman employee',
        'At least 2 members from employees committed to women\'s cause or having legal knowledge/experience',
        'One external member from NGO or association committed to women\'s issues',
        'At least half of the total members shall be women'
    ],
    'tenure': '3 years from the date of constitution',
    'key_provisions': [
        'Every organization with 10+ employees must have an ICC',
        'ICC must complete inquiry within 90 days',
        'Report must be submitted to employer within 10 days',
        'Employer must act on recommendations within 60 days',
        'Annual report must be filed by employer'
    ],
    'penalties': 'Non-compliance can result in penalty up to Rs. 50,000 and cancellation of license/registration for repeated violations'
}


@committees_bp.route('/')
@login_required
def index():
    """Main committees page with tabs."""
    tab = request.args.get('tab', 'posh')
    
    committee = None
    all_committees = []
    
    if tab == 'posh':
        committee = Committee.query.filter_by(
            committee_type='POSH',
            is_active=True
        ).first()
        all_committees = Committee.query.filter_by(
            committee_type='POSH'
        ).order_by(Committee.formed_on.desc()).all()
    elif tab == 'disc_action':
        committee = Committee.query.filter_by(
            committee_type='DISC_ACTION',
            is_active=True
        ).first()
        all_committees = Committee.query.filter_by(
            committee_type='DISC_ACTION'
        ).order_by(Committee.formed_on.desc()).all()
    elif tab == 'suspension':
        committee = Committee.query.filter_by(
            committee_type='SUSPENSION_REVIEW',
            is_active=True
        ).first()
        all_committees = Committee.query.filter_by(
            committee_type='SUSPENSION_REVIEW'
        ).order_by(Committee.formed_on.desc()).all()
    
    return render_template('committees/index.html',
                          active_tab=tab,
                          committee=committee,
                          all_committees=all_committees,
                          committee_types=COMMITTEE_TYPES)


@committees_bp.route('/posh')
@login_required
def posh_committee():
    """POSH Committee page."""
    # Get active POSH committee
    active_committee = Committee.query.filter_by(
        committee_type='POSH',
        is_active=True
    ).first()
    
    # Get all POSH committees (for history)
    all_committees = Committee.query.filter_by(
        committee_type='POSH'
    ).order_by(Committee.formed_on.desc()).all()
    
    return render_template('committees/posh.html',
                          committee=active_committee,
                          all_committees=all_committees,
                          posh_info=POSH_INFO,
                          committee_types=COMMITTEE_TYPES)


@committees_bp.route('/disc-action')
@login_required
def disc_action_committee():
    """Disciplinary Action Committee page."""
    active_committee = Committee.query.filter_by(
        committee_type='DISC_ACTION',
        is_active=True
    ).first()
    
    all_committees = Committee.query.filter_by(
        committee_type='DISC_ACTION'
    ).order_by(Committee.formed_on.desc()).all()
    
    return render_template('committees/disc_action.html',
                          committee=active_committee,
                          all_committees=all_committees,
                          committee_types=COMMITTEE_TYPES)


@committees_bp.route('/suspension-review')
@login_required
def suspension_review_committee():
    """Suspension Review Committee page."""
    active_committee = Committee.query.filter_by(
        committee_type='SUSPENSION_REVIEW',
        is_active=True
    ).first()
    
    all_committees = Committee.query.filter_by(
        committee_type='SUSPENSION_REVIEW'
    ).order_by(Committee.formed_on.desc()).all()
    
    return render_template('committees/suspension_review.html',
                          committee=active_committee,
                          all_committees=all_committees,
                          committee_types=COMMITTEE_TYPES)


@committees_bp.route('/create/<committee_type>', methods=['GET', 'POST'])
@login_required
@admin_required
def create_committee(committee_type):
    """Create a new committee."""
    if committee_type not in COMMITTEE_TYPES:
        flash('Invalid committee type.', 'danger')
        return redirect(url_for('committees.index'))
    
    if request.method == 'POST':
        order_number = request.form.get('order_number', '').strip()
        order_date = request.form.get('order_date', '').strip()
        formed_on = request.form.get('formed_on', '').strip()
        remarks = request.form.get('remarks', '').strip()
        
        # Convert date format from YYYY-MM-DD to DD-MM-YYYY
        if order_date:
            try:
                dt = datetime.strptime(order_date, '%Y-%m-%d')
                order_date = dt.strftime('%d-%m-%Y')
            except:
                pass
        
        if formed_on:
            try:
                dt = datetime.strptime(formed_on, '%Y-%m-%d')
                formed_on = dt.strftime('%d-%m-%Y')
                
                # For POSH, auto-calculate expiry (3 years)
                if committee_type == 'POSH':
                    expiry_dt = dt + timedelta(days=3*365)
                    expiry_date = expiry_dt.strftime('%d-%m-%Y')
                else:
                    expiry_date = request.form.get('expiry_date', '').strip()
                    if expiry_date:
                        try:
                            exp_dt = datetime.strptime(expiry_date, '%Y-%m-%d')
                            expiry_date = exp_dt.strftime('%d-%m-%Y')
                        except:
                            pass
            except:
                expiry_date = ''
        else:
            expiry_date = ''
        
        # Deactivate existing active committee of same type
        existing = Committee.query.filter_by(
            committee_type=committee_type,
            is_active=True
        ).first()
        if existing:
            existing.is_active = False
        
        # Create new committee
        committee = Committee(
            committee_type=committee_type,
            order_number=order_number,
            order_date=order_date,
            formed_on=formed_on,
            expiry_date=expiry_date,
            remarks=remarks,
            is_active=True
        )
        
        db.session.add(committee)
        db.session.commit()
        
        flash(f'{COMMITTEE_TYPES[committee_type]} created successfully!', 'success')
        
        # Redirect to add members
        return redirect(url_for('committees.manage_members', committee_id=committee.id))
    
    return render_template('committees/create.html',
                          committee_type=committee_type,
                          committee_type_name=COMMITTEE_TYPES[committee_type],
                          is_posh=(committee_type == 'POSH'))


@committees_bp.route('/<int:committee_id>/members', methods=['GET', 'POST'])
@login_required
@admin_required
def manage_members(committee_id):
    """Manage committee members."""
    committee = Committee.query.get_or_404(committee_id)
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'add':
            name = request.form.get('name', '').strip()
            designation = request.form.get('designation', '').strip()
            official_address = request.form.get('official_address', '').strip()
            position = request.form.get('position', '').strip()
            contact_number = request.form.get('contact_number', '').strip()
            email = request.form.get('email', '').strip()
            
            if name:
                # Get next order index
                max_order = db.session.query(db.func.max(CommitteeMember.order_index)).filter_by(
                    committee_id=committee_id
                ).scalar() or 0
                
                member = CommitteeMember(
                    committee_id=committee_id,
                    name=name,
                    designation=designation,
                    official_address=official_address,
                    position=position,
                    contact_number=contact_number,
                    email=email,
                    order_index=max_order + 1
                )
                db.session.add(member)
                db.session.commit()
                flash(f'Member "{name}" added successfully!', 'success')
        
        elif action == 'delete':
            member_id = request.form.get('member_id')
            if member_id:
                member = CommitteeMember.query.get(member_id)
                if member and member.committee_id == committee_id:
                    db.session.delete(member)
                    db.session.commit()
                    flash('Member removed successfully!', 'success')
        
        return redirect(url_for('committees.manage_members', committee_id=committee_id))
    
    members = CommitteeMember.query.filter_by(
        committee_id=committee_id
    ).order_by(CommitteeMember.order_index).all()
    
    # Position options based on committee type
    if committee.committee_type == 'POSH':
        positions = ['Presiding Officer', 'Member', 'External Member']
    else:
        positions = ['Chairperson', 'Member', 'Secretary']
    
    return render_template('committees/manage_members.html',
                          committee=committee,
                          members=members,
                          positions=positions,
                          committee_type_name=COMMITTEE_TYPES.get(committee.committee_type, 'Committee'))


@committees_bp.route('/<int:committee_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_committee(committee_id):
    """Edit committee details."""
    committee = Committee.query.get_or_404(committee_id)
    
    if request.method == 'POST':
        order_number = request.form.get('order_number', '').strip()
        order_date = request.form.get('order_date', '').strip()
        formed_on = request.form.get('formed_on', '').strip()
        remarks = request.form.get('remarks', '').strip()
        
        # Convert date format
        if order_date:
            try:
                dt = datetime.strptime(order_date, '%Y-%m-%d')
                order_date = dt.strftime('%d-%m-%Y')
            except:
                pass
        
        if formed_on:
            try:
                dt = datetime.strptime(formed_on, '%Y-%m-%d')
                formed_on = dt.strftime('%d-%m-%Y')
                
                if committee.committee_type == 'POSH':
                    expiry_dt = dt + timedelta(days=3*365)
                    expiry_date = expiry_dt.strftime('%d-%m-%Y')
                else:
                    expiry_date = request.form.get('expiry_date', '').strip()
                    if expiry_date:
                        try:
                            exp_dt = datetime.strptime(expiry_date, '%Y-%m-%d')
                            expiry_date = exp_dt.strftime('%d-%m-%Y')
                        except:
                            pass
            except:
                expiry_date = committee.expiry_date
        else:
            expiry_date = committee.expiry_date
        
        committee.order_number = order_number
        committee.order_date = order_date
        committee.formed_on = formed_on
        committee.expiry_date = expiry_date
        committee.remarks = remarks
        
        db.session.commit()
        flash('Committee updated successfully!', 'success')
        
        # Redirect based on committee type to main tab
        if committee.committee_type == 'POSH':
            return redirect(url_for('committees.index', tab='posh'))
        elif committee.committee_type == 'DISC_ACTION':
            return redirect(url_for('committees.index', tab='disc_action'))
        else:
            return redirect(url_for('committees.index', tab='suspension'))
    
    return render_template('committees/edit.html',
                          committee=committee,
                          committee_type_name=COMMITTEE_TYPES.get(committee.committee_type, 'Committee'),
                          is_posh=(committee.committee_type == 'POSH'))


@committees_bp.route('/<int:committee_id>/toggle-active', methods=['POST'])
@login_required
@admin_required
def toggle_active(committee_id):
    """Toggle committee active status."""
    committee = Committee.query.get_or_404(committee_id)
    
    if not committee.is_active:
        # Deactivate other active committees of same type
        existing = Committee.query.filter_by(
            committee_type=committee.committee_type,
            is_active=True
        ).first()
        if existing:
            existing.is_active = False
        
        committee.is_active = True
        flash('Committee set as active.', 'success')
    else:
        committee.is_active = False
        flash('Committee deactivated.', 'info')
    
    db.session.commit()
    return redirect(request.referrer or url_for('committees.index'))


@committees_bp.route('/<int:committee_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_committee(committee_id):
    """Delete a committee."""
    committee = Committee.query.get_or_404(committee_id)
    committee_type = committee.committee_type
    
    db.session.delete(committee)
    db.session.commit()
    
    flash('Committee deleted successfully!', 'success')
    
    if committee_type == 'POSH':
        return redirect(url_for('committees.index', tab='posh'))
    elif committee_type == 'DISC_ACTION':
        return redirect(url_for('committees.index', tab='disc_action'))
    else:
        return redirect(url_for('committees.index', tab='suspension'))


@committees_bp.route('/api/member/<int:member_id>', methods=['GET'])
@login_required
def get_member(member_id):
    """Get member details for editing."""
    member = CommitteeMember.query.get_or_404(member_id)
    return jsonify({
        'id': member.id,
        'name': member.name,
        'designation': member.designation,
        'official_address': member.official_address,
        'position': member.position,
        'contact_number': member.contact_number,
        'email': member.email
    })


@committees_bp.route('/api/member/<int:member_id>/update', methods=['POST'])
@login_required
@admin_required
def update_member(member_id):
    """Update member details."""
    member = CommitteeMember.query.get_or_404(member_id)
    
    data = request.get_json()
    member.name = data.get('name', member.name)
    member.designation = data.get('designation', member.designation)
    member.official_address = data.get('official_address', member.official_address)
    member.position = data.get('position', member.position)
    member.contact_number = data.get('contact_number', member.contact_number)
    member.email = data.get('email', member.email)
    
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Member updated successfully'})
