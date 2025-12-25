"""
RTI application routes for the Flask application.
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, Response
from flask_login import login_required, current_user
from models import RTIApplication, RTIAppeal, File
from extensions import db
from sqlalchemy import or_
import csv
import io

rti_bp = Blueprint('rti', __name__)


@rti_bp.route('/')
@login_required
def rti_index():
    """RTI Info main page with 3 tabs matching desktop app."""
    active_tab = request.args.get('tab', 'application')
    search = request.args.get('q', '').strip()
    
    # RTI Application Register
    app_query = RTIApplication.query
    if search and active_tab == 'application':
        app_query = app_query.filter(
            or_(
                RTIApplication.original_application_no.ilike(f'%{search}%'),
                RTIApplication.applicant_name.ilike(f'%{search}%'),
                RTIApplication.subject_of_information.ilike(f'%{search}%'),
                RTIApplication.file_number.ilike(f'%{search}%')
            )
        )
    applications = app_query.order_by(RTIApplication.id.desc()).all()
    
    # RTI Appeal Register
    appeal_query = RTIAppeal.query
    if search and active_tab == 'appeal':
        appeal_query = appeal_query.filter(
            or_(
                RTIAppeal.appeal_no.ilike(f'%{search}%'),
                RTIAppeal.original_application_no.ilike(f'%{search}%'),
                RTIAppeal.appellant_name.ilike(f'%{search}%')
            )
        )
    appeals = appeal_query.order_by(RTIAppeal.id.desc()).all()
    
    # RTI Fee Register (uses RTIApplication table with fee data)
    fee_query = RTIApplication.query.filter(
        or_(
            RTIApplication.fee_paid != None,
            RTIApplication.fee_paid > 0,
            RTIApplication.additional_amount_paid > 0,
            RTIApplication.receipt_no != None
        )
    )
    if search and active_tab == 'fee':
        fee_query = fee_query.filter(
            or_(
                RTIApplication.original_application_no.ilike(f'%{search}%'),
                RTIApplication.applicant_name.ilike(f'%{search}%'),
                RTIApplication.receipt_no.ilike(f'%{search}%'),
                RTIApplication.file_number.ilike(f'%{search}%')
            )
        )
    fee_entries = fee_query.order_by(RTIApplication.id.desc()).all()
    
    return render_template('rti/index.html',
                          active_tab=active_tab,
                          search=search,
                          applications=applications,
                          appeals=appeals,
                          fee_entries=fee_entries)


@rti_bp.route('/list')
@login_required
def list_rti():
    """List all RTI applications."""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Get filter parameters
    search_query = request.args.get('q', '').strip()
    status_filter = request.args.get('status', '')
    appeal_status = request.args.get('appeal_status', '')
    
    query = RTIApplication.query
    
    if search_query:
        query = query.filter(
            or_(
                RTIApplication.file_number.ilike(f'%{search_query}%'),
                RTIApplication.applicant_name.ilike(f'%{search_query}%'),
                RTIApplication.subject_of_information.ilike(f'%{search_query}%'),
                RTIApplication.original_application_no.ilike(f'%{search_query}%')
            )
        )
    
    if status_filter:
        query = query.filter(RTIApplication.status == status_filter)
    
    if appeal_status == 'Yes':
        query = query.filter(RTIApplication.appeal_submitted == 1)
    elif appeal_status == 'No':
        query = query.filter(or_(RTIApplication.appeal_submitted == 0, RTIApplication.appeal_submitted == None))
    
    # Order by id (no created_at in desktop database)
    query = query.order_by(RTIApplication.id.desc())
    
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    applications = pagination.items
    
    return render_template('rti/list.html', 
                          applications=applications, 
                          pagination=pagination,
                          search_query=search_query,
                          status_filter=status_filter,
                          appeal_status=appeal_status)


@rti_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_rti():
    """Create a new RTI application."""
    file_number = request.args.get('file_number', '') or request.form.get('file_number', '').strip()
    
    if request.method == 'POST':
        original_application_no = request.form.get('original_application_no', '').strip()
        
        if not original_application_no:
            flash('Application Number is required.', 'danger')
            existing_applications = RTIApplication.query.filter_by(file_number=file_number).order_by(RTIApplication.id.desc()).all() if file_number else []
            return render_template('rti/create.html', file_number=file_number, existing_applications=existing_applications)
        
        # Check if application number already exists
        existing_rti = RTIApplication.query.filter_by(original_application_no=original_application_no).first()
        if existing_rti:
            flash(f'RTI Application with number "{original_application_no}" already exists. Please use a different application number or edit the existing one.', 'danger')
            existing_applications = RTIApplication.query.filter_by(file_number=file_number).order_by(RTIApplication.id.desc()).all() if file_number else []
            return render_template('rti/create.html', file_number=file_number, existing_applications=existing_applications)
        
        # File number is optional
        if file_number:
            file = File.query.filter_by(file_number=file_number).first()
            if not file:
                flash(f'File "{file_number}" does not exist.', 'danger')
                existing_applications = RTIApplication.query.filter_by(file_number=file_number).order_by(RTIApplication.id.desc()).all() if file_number else []
                return render_template('rti/create.html', file_number=file_number, existing_applications=existing_applications)
        
        # Parse fee values
        fee_paid = 0
        try:
            fee_paid = float(request.form.get('fee_paid', 0) or 0)
        except ValueError:
            pass
        
        additional_amount = 0
        try:
            additional_amount = float(request.form.get('additional_amount_paid', 0) or 0)
        except ValueError:
            pass
        
        rti = RTIApplication(
            file_number=file_number if file_number else None,
            sl_no=request.form.get('sl_no', ''),
            original_application_no=original_application_no,
            date_of_receipt=request.form.get('date_of_receipt', ''),
            applicant_prefix=request.form.get('applicant_prefix', 'Sri.'),
            applicant_name=request.form.get('applicant_name', ''),
            address=request.form.get('address', ''),
            subject_of_information=request.form.get('subject_of_information', ''),
            fee_paid=fee_paid,
            mode_of_payment=request.form.get('mode_of_payment', 'Cash'),
            additional_amount_paid=additional_amount,
            receipt_no=request.form.get('receipt_no', ''),
            date_of_acknowledgment=request.form.get('date_of_acknowledgment', ''),
            date_of_disposal=request.form.get('date_of_disposal', ''),
            status=request.form.get('status', 'Not replied'),
            remarks=request.form.get('remarks', ''),
            appeal_submitted='appeal_submitted' in request.form
        )
        
        db.session.add(rti)
        db.session.commit()
        
        flash('RTI application created successfully.', 'success')
        
        # If file_number was provided, redirect back to the RTI window for that file
        if file_number:
            return redirect(url_for('rti.create_rti', file_number=file_number))
        return redirect(url_for('rti.view_rti', id=rti.id))
    
    # Get file number from query params if provided
    file_number = request.args.get('file_number', '')
    
    # Get existing RTI applications for this file
    existing_applications = []
    if file_number:
        existing_applications = RTIApplication.query.filter_by(file_number=file_number).order_by(RTIApplication.id.desc()).all()
    
    return render_template('rti/create.html', file_number=file_number, existing_applications=existing_applications)


@rti_bp.route('/<int:id>/json')
@login_required
def get_rti_json(id):
    """Get RTI application data as JSON for editing."""
    application = RTIApplication.query.get_or_404(id)
    return jsonify({
        'success': True,
        'application': {
            'id': application.id,
            'file_number': application.file_number or '',
            'sl_no': application.sl_no or '',
            'original_application_no': application.original_application_no or '',
            'date_of_receipt': application.date_of_receipt or '',
            'applicant_prefix': application.applicant_prefix or 'Sri.',
            'applicant_name': application.applicant_name or '',
            'address': application.address or '',
            'subject_of_information': application.subject_of_information or '',
            'fee_paid': application.fee_paid or 0,
            'mode_of_payment': application.mode_of_payment or 'Cash',
            'additional_amount_paid': application.additional_amount_paid or 0,
            'receipt_no': application.receipt_no or '',
            'date_of_acknowledgment': application.date_of_acknowledgment or '',
            'date_of_disposal': application.date_of_disposal or '',
            'status': application.status or 'Not replied',
            'remarks': application.remarks or '',
            'appeal_submitted': application.appeal_submitted or False
        }
    })


@rti_bp.route('/<int:id>')
@login_required
def view_rti(id):
    """View RTI application details."""
    application = RTIApplication.query.get_or_404(id)
    appeals = RTIAppeal.query.filter_by(rti_application_id=id).order_by(RTIAppeal.id.desc()).all()
    
    return render_template('rti/view.html', application=application, appeals=appeals)


@rti_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_rti(id):
    """Edit RTI application."""
    application = RTIApplication.query.get_or_404(id)
    
    if request.method == 'POST':
        application.sl_no = request.form.get('sl_no', '')
        application.original_application_no = request.form.get('original_application_no', '')
        application.date_of_receipt = request.form.get('date_of_receipt', '')
        application.applicant_prefix = request.form.get('applicant_prefix', 'Sri.')
        application.applicant_name = request.form.get('applicant_name', '')
        application.address = request.form.get('address', '')
        application.subject_of_information = request.form.get('subject_of_information', '')
        
        try:
            application.fee_paid = float(request.form.get('fee_paid', 0) or 0)
        except ValueError:
            application.fee_paid = 0
        
        application.mode_of_payment = request.form.get('mode_of_payment', 'Cash')
        
        try:
            application.additional_amount_paid = float(request.form.get('additional_amount_paid', 0) or 0)
        except ValueError:
            application.additional_amount_paid = 0
        
        application.receipt_no = request.form.get('receipt_no', '')
        application.date_of_acknowledgment = request.form.get('date_of_acknowledgment', '')
        application.date_of_disposal = request.form.get('date_of_disposal', '')
        application.status = request.form.get('status', 'Not replied')
        application.remarks = request.form.get('remarks', '')
        application.appeal_submitted = 'appeal_submitted' in request.form
        
        db.session.commit()
        
        flash('RTI application updated successfully.', 'success')
        
        # Check if came from RTI window (file context)
        if application.file_number:
            return redirect(url_for('rti.create_rti', file_number=application.file_number))
        return redirect(url_for('rti.view_rti', id=id))
    
    return render_template('rti/edit.html', application=application)


@rti_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete_rti(id):
    """Delete RTI application."""
    if not current_user.is_admin():
        flash('Only administrators can delete RTI applications.', 'danger')
        return redirect(url_for('rti.view_rti', id=id))
    
    application = RTIApplication.query.get_or_404(id)
    file_number = application.file_number
    
    db.session.delete(application)
    db.session.commit()
    
    flash('RTI application deleted successfully.', 'success')
    
    # Redirect back to RTI window if file number exists
    if file_number:
        return redirect(url_for('rti.create_rti', file_number=file_number))
    return redirect(url_for('rti.rti_index'))


# RTI Appeal routes
@rti_bp.route('/<int:rti_id>/appeal/create', methods=['GET', 'POST'])
@login_required
def create_appeal(rti_id):
    """Create a new RTI appeal."""
    application = RTIApplication.query.get_or_404(rti_id)
    
    if request.method == 'POST':
        appeal = RTIAppeal(
            rti_application_id=rti_id,
            sl_no=request.form.get('sl_no', ''),
            appeal_no=request.form.get('appeal_no', ''),
            original_application_no=application.original_application_no,
            date_of_receipt=request.form.get('date_of_receipt', ''),
            appellant_prefix=request.form.get('appellant_prefix', 'Sri.'),
            appellant_name=request.form.get('appellant_name', '') or application.applicant_name,
            date_of_spio_response=request.form.get('date_of_spio_response', '') if request.form.get('spio_response_checkbox') else '',
            date_of_hearing=request.form.get('date_of_hearing', '') if request.form.get('hearing_checkbox') else '',
            date_of_disposal=request.form.get('date_of_disposal', '') if request.form.get('disposal_checkbox') else '',
            outcome=request.form.get('outcome', ''),
            remarks=request.form.get('remarks', '')
        )
        
        db.session.add(appeal)
        
        # Update RTI application appeal status
        application.appeal_submitted = True
        
        db.session.commit()
        
        flash('RTI appeal created successfully.', 'success')
        # Stay on the appeal window after save
        return redirect(url_for('rti.create_appeal', rti_id=rti_id))
    
    # Get existing appeals for this RTI application
    existing_appeals = RTIAppeal.query.filter_by(rti_application_id=rti_id).all()
    
    return render_template('rti/create_appeal.html', 
                         application=application,
                         existing_appeals=existing_appeals)


@rti_bp.route('/appeal/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_appeal(id):
    """Edit RTI appeal."""
    appeal = RTIAppeal.query.get_or_404(id)
    application = RTIApplication.query.get_or_404(appeal.rti_application_id)
    
    if request.method == 'POST':
        appeal.sl_no = request.form.get('sl_no', '')
        appeal.appeal_no = request.form.get('appeal_no', '')
        appeal.date_of_receipt = request.form.get('date_of_receipt', '')
        appeal.appellant_prefix = request.form.get('appellant_prefix', 'Sri.')
        appeal.appellant_name = request.form.get('appellant_name', '')
        appeal.date_of_spio_response = request.form.get('date_of_spio_response', '') if request.form.get('spio_response_checkbox') else ''
        appeal.date_of_hearing = request.form.get('date_of_hearing', '') if request.form.get('hearing_checkbox') else ''
        appeal.date_of_disposal = request.form.get('date_of_disposal', '') if request.form.get('disposal_checkbox') else ''
        appeal.outcome = request.form.get('outcome', '')
        appeal.remarks = request.form.get('remarks', '')
        
        db.session.commit()
        
        flash('RTI appeal updated successfully.', 'success')
        # Stay on the appeal window after save
        return redirect(url_for('rti.create_appeal', rti_id=appeal.rti_application_id))
    
    return render_template('rti/edit_appeal.html', appeal=appeal, application=application)


@rti_bp.route('/appeal/<int:id>/json')
@login_required
def get_appeal_json(id):
    """Get RTI appeal data as JSON for AJAX loading."""
    appeal = RTIAppeal.query.get_or_404(id)
    return jsonify({
        'success': True,
        'appeal': {
            'id': appeal.id,
            'sl_no': appeal.sl_no or '',
            'appeal_no': appeal.appeal_no or '',
            'original_application_no': appeal.original_application_no or '',
            'date_of_receipt': appeal.date_of_receipt or '',
            'appellant_prefix': appeal.appellant_prefix or 'Sri.',
            'appellant_name': appeal.appellant_name or '',
            'date_of_spio_response': appeal.date_of_spio_response or '',
            'date_of_hearing': appeal.date_of_hearing or '',
            'date_of_disposal': appeal.date_of_disposal or '',
            'outcome': appeal.outcome or '',
            'remarks': appeal.remarks or ''
        }
    })


@rti_bp.route('/appeal/<int:id>/delete', methods=['POST'])
@login_required
def delete_appeal(id):
    """Delete RTI appeal."""
    if not current_user.is_admin():
        flash('Only administrators can delete appeals.', 'danger')
        return redirect(url_for('rti.rti_index'))
    
    appeal = RTIAppeal.query.get_or_404(id)
    rti_id = appeal.rti_application_id
    
    db.session.delete(appeal)
    db.session.commit()
    
    flash('RTI appeal deleted successfully.', 'success')
    # Stay on appeal window after delete
    return redirect(url_for('rti.create_appeal', rti_id=rti_id))


@rti_bp.route('/export')
@login_required
def export_rti():
    """Redirect to export applications."""
    return redirect(url_for('rti.export_applications'))


@rti_bp.route('/export/applications')
@login_required
def export_applications():
    """Export RTI Application Register to CSV."""
    applications = RTIApplication.query.order_by(RTIApplication.id.desc()).all()
    
    output = io.StringIO()
    # Add UTF-8 BOM for Excel to recognize Unicode characters (Malayalam etc.)
    output.write('\ufeff')
    writer = csv.writer(output)
    
    # Write header matching desktop app columns
    writer.writerow([
        'Sl.No.', 'Original Application No.', 'Date of Receipt', "Applicant's Name", 
        'Address', 'Subject of Information', 'Fee Paid (₹)', 'Mode of Payment',
        'Date of Acknowledgment', 'Date of Disposal', 'Status', 'Remarks', 'File Number'
    ])
    
    # Write data
    for i, app in enumerate(applications, 1):
        writer.writerow([
            app.sl_no or i,
            app.original_application_no or '',
            app.date_of_receipt or '',
            f"{app.applicant_prefix or ''} {app.applicant_name or ''}".strip(),
            app.address or '',
            app.subject_of_information or '',
            app.fee_paid or '',
            app.mode_of_payment or '',
            app.date_of_acknowledgment or '',
            app.date_of_disposal or '',
            app.status or '',
            app.remarks or '',
            app.file_number or ''
        ])
    
    output.seek(0)
    
    return Response(
        output.getvalue().encode('utf-8-sig'),
        mimetype='text/csv; charset=utf-8-sig',
        headers={'Content-Disposition': 'attachment; filename=RTI_Applications.csv'}
    )


@rti_bp.route('/export/appeals')
@login_required
def export_appeals():
    """Export RTI Appeal Register to CSV."""
    appeals = RTIAppeal.query.order_by(RTIAppeal.id.desc()).all()
    
    output = io.StringIO()
    # Add UTF-8 BOM for Excel to recognize Unicode characters (Malayalam etc.)
    output.write('\ufeff')
    writer = csv.writer(output)
    
    # Write header matching desktop app columns
    writer.writerow([
        'Sl.No.', 'Appeal No.', 'Original Application No.', 'Date of Receipt', 
        "Appellant's Name", 'Date of SPIO Response', 'Date of Hearing', 
        'Date of Disposal', 'Outcome', 'Remarks', 'File Number'
    ])
    
    # Write data
    for i, appeal in enumerate(appeals, 1):
        file_number = ''
        if appeal.application:
            file_number = appeal.application.file_number or ''
        writer.writerow([
            appeal.sl_no or i,
            appeal.appeal_no or '',
            appeal.original_application_no or '',
            appeal.date_of_receipt or '',
            f"{appeal.appellant_prefix or ''} {appeal.appellant_name or ''}".strip(),
            appeal.date_of_spio_response or '',
            appeal.date_of_hearing or '',
            appeal.date_of_disposal or '',
            appeal.outcome or '',
            appeal.remarks or '',
            file_number
        ])
    
    output.seek(0)
    
    return Response(
        output.getvalue().encode('utf-8-sig'),
        mimetype='text/csv; charset=utf-8-sig',
        headers={'Content-Disposition': 'attachment; filename=RTI_Appeals.csv'}
    )


@rti_bp.route('/export/fees')
@login_required
def export_fees():
    """Export RTI Fee Register to CSV."""
    fee_entries = RTIApplication.query.filter(
        or_(
            RTIApplication.fee_paid != None,
            RTIApplication.fee_paid > 0,
            RTIApplication.additional_amount_paid > 0,
            RTIApplication.receipt_no != None
        )
    ).order_by(RTIApplication.id.desc()).all()
    
    output = io.StringIO()
    # Add UTF-8 BOM for Excel to recognize Unicode characters (Malayalam etc.)
    output.write('\ufeff')
    writer = csv.writer(output)
    
    # Write header matching desktop app columns
    writer.writerow([
        'Sl.No.', 'Application No.', "Applicant's Name", 'Fee Paid (Rs.)', 
        'Mode of Payment', 'Date of Payment', 'Receipt No.', 
        'Additional Fee (Rs.)', 'Purpose', 'Remarks', 'File Number'
    ])
    
    # Write data
    for i, fee in enumerate(fee_entries, 1):
        writer.writerow([
            fee.sl_no or i,
            fee.original_application_no or '',
            f"{fee.applicant_prefix or ''} {fee.applicant_name or ''}".strip(),
            fee.fee_paid or '',
            fee.mode_of_payment or '',
            fee.date_of_receipt or '',
            fee.receipt_no or '',
            fee.additional_amount_paid or '',
            fee.subject_of_information or '',  # Purpose
            fee.remarks or '',
            fee.file_number or ''
        ])
    
    output.seek(0)
    
    return Response(
        output.getvalue().encode('utf-8-sig'),
        mimetype='text/csv; charset=utf-8-sig',
        headers={'Content-Disposition': 'attachment; filename=RTI_Fees.csv'}
    )


@rti_bp.route('/pending')
@login_required
def pending_rti():
    """List pending RTI applications."""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    query = RTIApplication.query.filter(RTIApplication.status != 'Disposed')
    query = query.order_by(RTIApplication.received_date.asc())
    
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    applications = pagination.items
    
    return render_template('rti/pending.html', 
                          applications=applications, 
                          pagination=pagination)


@rti_bp.route('/appeals')
@login_required
def list_appeals():
    """List all RTI appeals."""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    search_query = request.args.get('q', '').strip()
    
    query = db.session.query(RTIAppeal, RTIApplication).join(
        RTIApplication, RTIAppeal.rti_application_id == RTIApplication.id
    )
    
    if search_query:
        query = query.filter(
            or_(
                RTIApplication.file_number.ilike(f'%{search_query}%'),
                RTIAppeal.appellant_name.ilike(f'%{search_query}%'),
                RTIAppeal.appeal_no.ilike(f'%{search_query}%'),
                RTIAppeal.original_application_no.ilike(f'%{search_query}%')
            )
        )
    
    query = query.order_by(RTIAppeal.id.desc())
    
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    results = pagination.items
    
    return render_template('rti/appeals.html', 
                          results=results, 
                          pagination=pagination,
                          search_query=search_query)
