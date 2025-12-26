"""
Database models for the Vigilance File Management System.
"""
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db, login_manager


class User(UserMixin, db.Model):
    """User model for authentication."""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default='guest')  # admin, guest
    email = db.Column(db.String(120), unique=True, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        return self.role == 'admin'
    
    def __repr__(self):
        return f'<User {self.username}>'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class File(db.Model):
    """Main file model - matches desktop database schema."""
    __tablename__ = 'files'
    
    # Desktop uses file_number as primary key (TEXT PRIMARY KEY)
    file_number = db.Column(db.String(100), primary_key=True)
    file_type = db.Column(db.String(50))  # Physical, E-Office
    subject = db.Column(db.Text)
    details_of_file = db.Column(db.Text)
    status = db.Column(db.String(50))
    category = db.Column(db.Text)  # JSON string - multiple categories
    type_of_file = db.Column(db.Text)  # JSON string - multiple types
    disciplinary_action = db.Column(db.String(10))  # Yes/No
    institution_type = db.Column(db.String(100))
    institution_name = db.Column(db.String(200))
    follow_up_date = db.Column(db.String(20))
    remarks = db.Column(db.Text)
    is_closed = db.Column(db.Integer, default=0)  # 0 for active, 1 for closed (INTEGER in desktop)
    closed_date = db.Column(db.String(20))
    closing_remarks = db.Column(db.Text)
    
    # Physical file location
    almirah = db.Column(db.String(50))
    rack = db.Column(db.String(20))
    row = db.Column(db.String(20))
    
    # E-Office migration
    migrated_to_eoffice = db.Column(db.String(10))
    eoffice_file_number = db.Column(db.String(100))
    original_file_number = db.Column(db.String(100))
    
    # Timestamps
    file_year = db.Column(db.String(10))
    last_modified = db.Column(db.String(50))  # TEXT in desktop
    
    # Relationships
    disciplinary_actions = db.relationship('DisciplinaryAction', backref='file', lazy='dynamic', cascade='all, delete-orphan')
    pr_entries = db.relationship('PREntry', backref='file', lazy='dynamic', cascade='all, delete-orphan')
    rti_applications = db.relationship('RTIApplication', backref='file', lazy='dynamic', cascade='all, delete-orphan')
    court_cases = db.relationship('CourtCase', backref='file', lazy='dynamic', cascade='all, delete-orphan')
    inquiry_details = db.relationship('InquiryDetails', backref='file', uselist=False, cascade='all, delete-orphan')
    
    # Helper property for Flask-SQLAlchemy compatibility
    @property
    def id(self):
        """Return file_number as id for compatibility."""
        return self.file_number
    
    def __repr__(self):
        return f'<File {self.file_number}>'


class Institution(db.Model):
    """Institution model - matches desktop database schema."""
    __tablename__ = 'institutions'
    
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(100))
    name = db.Column(db.String(200))
    address = db.Column(db.Text)
    contact_number = db.Column(db.String(50))
    email = db.Column(db.String(120))
    head_of_institution = db.Column(db.String(100))
    head_name = db.Column(db.String(100))
    head_contact = db.Column(db.String(50))
    staff_details = db.Column(db.Text)  # JSON string
    
    def get_staff_list(self):
        """Parse and return staff_details as a list of dictionaries."""
        import json
        if not self.staff_details:
            return []
        try:
            return json.loads(self.staff_details)
        except (json.JSONDecodeError, TypeError):
            return []
    
    def __repr__(self):
        return f'<Institution {self.name}>'


class Employee(db.Model):
    """Employee model - matches desktop database schema."""
    __tablename__ = 'employees'
    
    # Desktop uses pen as primary key (TEXT PRIMARY KEY)
    pen = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.String(200))
    date_of_birth = db.Column(db.String(20))
    designation = db.Column(db.String(100))
    joining_date = db.Column(db.String(20))
    institution_name = db.Column(db.String(200))
    permanent_address = db.Column(db.Text)
    communication_address = db.Column(db.Text)
    
    # Helper property for Flask-SQLAlchemy compatibility
    @property
    def id(self):
        """Return pen as id for compatibility."""
        return self.pen
    
    def __repr__(self):
        return f'<Employee {self.pen} - {self.name}>'


class DisciplinaryAction(db.Model):
    """Disciplinary action details model."""
    __tablename__ = 'disciplinary_action_details'
    
    id = db.Column(db.Integer, primary_key=True)
    file_number = db.Column(db.String(100), db.ForeignKey('files.file_number'), nullable=False)
    employee_name = db.Column(db.String(200))
    pen = db.Column(db.String(50))
    designation = db.Column(db.String(100))
    institution = db.Column(db.String(200))
    entry_cadre = db.Column(db.String(100))
    joining_date = db.Column(db.String(20))
    service_regularised = db.Column(db.String(10))
    date_regularisation = db.Column(db.String(20))
    probation = db.Column(db.String(50))
    date_probation_declared = db.Column(db.String(20))
    date_superannuation = db.Column(db.String(20))
    unauthorised_others = db.Column(db.String(50))
    probation_termination_notice = db.Column(db.String(50))
    ptn_reply_received = db.Column(db.String(10))
    ptn_reply_date = db.Column(db.String(20))
    action_taking_office = db.Column(db.String(50))
    
    # MOC details
    moc_issued = db.Column(db.String(50))
    moc_issued_by = db.Column(db.String(50))
    major_minor = db.Column(db.String(20))
    moc_number = db.Column(db.String(100))
    moc_date = db.Column(db.String(20))
    moc_receipt_date = db.Column(db.String(20))
    
    # WSD details
    wsd_received_date = db.Column(db.String(20))
    wsd_letter_no = db.Column(db.String(100))
    
    # SCN details
    scn_issued_date = db.Column(db.String(20))
    scn_issued_by = db.Column(db.String(50))
    scn_receipt_date = db.Column(db.String(20))
    scn_reply_date = db.Column(db.String(20))
    
    # DHS details
    moc_received_at_dmo_date = db.Column(db.String(20))
    moc_received_letter_no = db.Column(db.String(100))
    moc_sent_to_dhs_date = db.Column(db.String(20))
    wsd_sent_to_dhs_date = db.Column(db.String(20))
    wsd_sent_letter_no = db.Column(db.String(100))
    scn_received_at_dmo_date = db.Column(db.String(20))
    scn_reply_sent_to_dhs_date = db.Column(db.String(20))
    dhs_file_number = db.Column(db.String(100))
    
    finalised_date = db.Column(db.String(20))
    moc_receipt_sent_to_dhs_date = db.Column(db.String(20))
    scn_receipt_sent_to_dhs_date = db.Column(db.String(20))
    modified_date = db.Column(db.String(20))
    
    def __repr__(self):
        return f'<DisciplinaryAction {self.file_number} - {self.pen}>'


class UnauthorisedAbsentee(db.Model):
    """Unauthorised absentee details model."""
    __tablename__ = 'unauthorised_absentees'
    
    id = db.Column(db.Integer, primary_key=True)
    da_id = db.Column(db.Integer, db.ForeignKey('disciplinary_action_details.id'), unique=True)
    date_from_ua = db.Column(db.String(20))
    willingness = db.Column(db.String(50))
    bond_submitted = db.Column(db.String(10))
    communication_address = db.Column(db.Text)
    date_reported_to_dmo = db.Column(db.String(20))
    letter_no_reported_to_dmo = db.Column(db.String(100))
    date_reported_to_dhs = db.Column(db.String(20))
    letter_no_reported_to_dhs = db.Column(db.String(100))
    weather_reported_to_dhs = db.Column(db.String(10))
    present_status = db.Column(db.String(100))
    disc_action_status = db.Column(db.String(100))
    
    disciplinary_action = db.relationship('DisciplinaryAction', backref=db.backref('ua_details', uselist=False))
    
    def __repr__(self):
        return f'<UnauthorisedAbsentee {self.da_id}>'


class PREntry(db.Model):
    """PR (Paper Register) Entry model."""
    __tablename__ = 'pr_entries'
    
    id = db.Column(db.Integer, primary_key=True)
    file_number = db.Column(db.String(100), db.ForeignKey('files.file_number'), nullable=False)
    serial_number = db.Column(db.String(50))
    current_number = db.Column(db.String(50))
    date_receipt_clerk = db.Column(db.String(20))
    title = db.Column(db.Text)
    from_whom_outside_name = db.Column(db.String(200))
    from_whom_outside_number = db.Column(db.String(100))
    from_whom_outside_date = db.Column(db.String(20))
    submitted_by_clerk_date = db.Column(db.String(20))
    return_to_clerk_date = db.Column(db.String(20))
    reference_issued_to_whom = db.Column(db.String(200))
    reference_issued_date = db.Column(db.String(20))
    reply_fresh_current_from_whom = db.Column(db.String(200))
    reply_fresh_current_number = db.Column(db.String(100))
    reply_fresh_current_date = db.Column(db.String(20))
    date_receipt_clerk_fresh = db.Column(db.String(20))
    disposal_nature = db.Column(db.String(100))
    disposal_date = db.Column(db.String(20))
    
    def __repr__(self):
        return f'<PREntry {self.file_number} - {self.serial_number}>'


class RTIApplication(db.Model):
    """RTI Application model."""
    __tablename__ = 'rti_applications'
    
    id = db.Column(db.Integer, primary_key=True)
    file_number = db.Column(db.String(100), db.ForeignKey('files.file_number'), nullable=True)
    sl_no = db.Column(db.String(20))
    original_application_no = db.Column(db.String(100), unique=True)
    date_of_receipt = db.Column(db.String(20))
    applicant_prefix = db.Column(db.String(20))
    applicant_name = db.Column(db.String(200))
    address = db.Column(db.Text)
    subject_of_information = db.Column(db.Text)
    fee_paid = db.Column(db.Float, default=0)
    mode_of_payment = db.Column(db.String(50))
    additional_amount_paid = db.Column(db.Float, default=0)
    receipt_no = db.Column(db.String(100))
    date_of_acknowledgment = db.Column(db.String(20))
    date_of_disposal = db.Column(db.String(20))
    status = db.Column(db.String(50))
    remarks = db.Column(db.Text)
    appeal_submitted = db.Column(db.Boolean, default=False)
    
    appeals = db.relationship('RTIAppeal', backref='application', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<RTIApplication {self.original_application_no}>'


class RTIAppeal(db.Model):
    """RTI Appeal model."""
    __tablename__ = 'rti_appeals'
    
    id = db.Column(db.Integer, primary_key=True)
    rti_application_id = db.Column(db.Integer, db.ForeignKey('rti_applications.id'))
    sl_no = db.Column(db.String(20))
    appeal_no = db.Column(db.String(100), unique=True)
    original_application_no = db.Column(db.String(100))
    date_of_receipt = db.Column(db.String(20))
    appellant_prefix = db.Column(db.String(20))
    appellant_name = db.Column(db.String(200))
    date_of_spio_response = db.Column(db.String(20))
    date_of_hearing = db.Column(db.String(20))
    date_of_disposal = db.Column(db.String(20))
    outcome = db.Column(db.String(100))
    remarks = db.Column(db.Text)
    
    def __repr__(self):
        return f'<RTIAppeal {self.appeal_no}>'


class CourtCase(db.Model):
    """Court case details model."""
    __tablename__ = 'court_case_details'
    
    id = db.Column(db.Integer, primary_key=True)
    file_number = db.Column(db.String(100), db.ForeignKey('files.file_number'), nullable=False)
    name_of_forum = db.Column(db.String(200))
    forum_specify = db.Column(db.String(200))
    case_no = db.Column(db.String(100))
    month = db.Column(db.String(20))
    year = db.Column(db.String(10))
    receipt_date = db.Column(db.String(20))
    related_to_mo = db.Column(db.String(10))
    mo_pen = db.Column(db.String(50))
    sf_forwarded = db.Column(db.String(10))
    sf_forwarding_date = db.Column(db.String(20))
    affidavit_filed = db.Column(db.String(10))
    affidavit_filed_date = db.Column(db.String(20))
    present_status = db.Column(db.String(100))
    disposed_against_dhs = db.Column(db.String(10))
    disposal_date = db.Column(db.String(20))
    appeal_scope_asked = db.Column(db.String(10))
    letter_to_dhs_date = db.Column(db.String(20))
    complied_with_orders = db.Column(db.String(10))
    incompliance_details = db.Column(db.Text)
    appeal_filed = db.Column(db.String(10))
    appeal_follow_up_done = db.Column(db.String(10))
    contempt_on_case = db.Column(db.String(10))
    contempt_details = db.Column(db.Text)
    action_taken_on_contempt = db.Column(db.Text)
    office_section_dhs_checked = db.Column(db.Boolean, default=False)
    office_section_dhs = db.Column(db.String(200))
    remarks = db.Column(db.Text)
    
    def __repr__(self):
        return f'<CourtCase {self.file_number} - {self.case_no}>'


class InquiryDetails(db.Model):
    """Inquiry details model."""
    __tablename__ = 'inquiry_details'
    
    id = db.Column(db.Integer, primary_key=True)
    file_number = db.Column(db.String(100), db.ForeignKey('files.file_number'), unique=True, nullable=False)
    
    # Preliminary inquiry (Integer for PostgreSQL compatibility - 0/1)
    prelim_conducted = db.Column(db.Integer, default=0)
    prelim_io_name = db.Column(db.String(200))
    prelim_inquiry_date = db.Column(db.String(20))
    prelim_venue = db.Column(db.String(200))
    prelim_report_submitted = db.Column(db.Integer, default=0)
    prelim_report_to = db.Column(db.String(200))
    prelim_report_date = db.Column(db.String(20))
    
    # Rule 15(ii) inquiry (Integer for PostgreSQL compatibility - 0/1)
    rule15_conducted = db.Column(db.Integer, default=0)
    rule15_io_name = db.Column(db.String(200))
    rule15_inquiry_date = db.Column(db.String(20))
    rule15_venue = db.Column(db.String(200))
    rule15_report_submitted = db.Column(db.Integer, default=0)
    rule15_report_to = db.Column(db.String(200))
    rule15_report_date = db.Column(db.String(20))
    
    def __repr__(self):
        return f'<InquiryDetails {self.file_number}>'


class WomenHarassmentCase(db.Model):
    """Women harassment case model."""
    __tablename__ = 'women_harassment_cases'
    
    id = db.Column(db.Integer, primary_key=True)
    file_number = db.Column(db.String(100), db.ForeignKey('files.file_number'), unique=True, nullable=False)
    icc_report_attached = db.Column(db.Boolean, default=False)
    icc_report_date = db.Column(db.String(20))
    finalised = db.Column(db.Boolean, default=False)
    finalised_date = db.Column(db.String(20))
    
    employees_involved = db.relationship('WHEmployeeInvolved', backref='case', lazy='dynamic', cascade='all, delete-orphan')
    culprits_involved = db.relationship('WHCulpritInvolved', backref='case', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<WomenHarassmentCase {self.file_number}>'


class WHEmployeeInvolved(db.Model):
    """Women harassment - employees involved."""
    __tablename__ = 'wh_employees_involved'
    
    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.Integer, db.ForeignKey('women_harassment_cases.id'))
    pen = db.Column(db.String(50))
    name = db.Column(db.String(200))
    designation = db.Column(db.String(100))
    institution = db.Column(db.String(200))
    
    def __repr__(self):
        return f'<WHEmployeeInvolved {self.name}>'


class WHCulpritInvolved(db.Model):
    """Women harassment - culprits involved."""
    __tablename__ = 'wh_culprits_involved'
    
    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.Integer, db.ForeignKey('women_harassment_cases.id'))
    pen = db.Column(db.String(50))
    name = db.Column(db.String(200))
    designation = db.Column(db.String(100))
    institution = db.Column(db.String(200))
    
    def __repr__(self):
        return f'<WHCulpritInvolved {self.name}>'


class ComplaintDetails(db.Model):
    """Complaint details model."""
    __tablename__ = 'complaint_details'
    
    id = db.Column(db.Integer, primary_key=True)
    file_number = db.Column(db.String(100), db.ForeignKey('files.file_number'), unique=True, nullable=False)
    plaintiff_type = db.Column(db.String(50))
    plaintiff_pen = db.Column(db.String(50))
    plaintiff_name = db.Column(db.String(200))
    plaintiff_address = db.Column(db.Text)
    plaintiff_contact_number = db.Column(db.String(50))
    plaintiff_email = db.Column(db.String(120))
    respondent_type = db.Column(db.String(50))
    respondent_pen = db.Column(db.String(50))
    respondent_name = db.Column(db.String(200))
    respondent_address = db.Column(db.Text)
    respondent_contact_number = db.Column(db.String(50))
    respondent_email = db.Column(db.String(120))
    
    def __repr__(self):
        return f'<ComplaintDetails {self.file_number}>'


class ReportSoughtDetails(db.Model):
    """Report sought details model."""
    __tablename__ = 'report_sought_details'
    
    id = db.Column(db.Integer, primary_key=True)
    file_number = db.Column(db.String(100), db.ForeignKey('files.file_number'), nullable=False)
    subject = db.Column(db.Text)
    body = db.Column(db.String(100))
    report_sought_date = db.Column(db.String(20))
    status = db.Column(db.String(50))
    institution = db.Column(db.String(200))
    details = db.Column(db.Text)
    submitted = db.Column(db.String(10), default='No')
    submitted_date = db.Column(db.String(20))
    
    def __repr__(self):
        return f'<ReportSoughtDetails {self.file_number}>'


class ReportAskedDetails(db.Model):
    """Report asked details model."""
    __tablename__ = 'report_asked_details'
    
    id = db.Column(db.Integer, primary_key=True)
    file_number = db.Column(db.String(100), db.ForeignKey('files.file_number'), nullable=False)
    whether_report_asked = db.Column(db.String(10))
    asked_date = db.Column(db.String(20))
    institution_name = db.Column(db.String(200))
    report_submitted = db.Column(db.String(10))
    received_date = db.Column(db.String(20))
    
    def __repr__(self):
        return f'<ReportAskedDetails {self.file_number}>'


class SocialSecurityPension(db.Model):
    """Social security pension details model."""
    __tablename__ = 'social_security_pension_details'
    
    id = db.Column(db.Integer, primary_key=True)
    file_number = db.Column(db.String(100), db.ForeignKey('files.file_number'), unique=True, nullable=False)
    main_list_sl_no = db.Column(db.String(50))
    pen = db.Column(db.String(50))
    name = db.Column(db.String(200))
    sevana_pensioner_id = db.Column(db.String(100))
    aadhar_no = db.Column(db.String(20))
    amount = db.Column(db.Float, default=0)
    refunded_status = db.Column(db.String(10))
    refunded_amount = db.Column(db.Float, default=0)
    letter_no = db.Column(db.String(100))
    letter_date = db.Column(db.String(20))
    receipt_no = db.Column(db.String(100))
    finalised = db.Column(db.String(10))
    finalised_date = db.Column(db.String(20))
    
    def __repr__(self):
        return f'<SocialSecurityPension {self.file_number}>'


class RemarksEntry(db.Model):
    """Remarks entries model."""
    __tablename__ = 'remarks_entries'
    
    id = db.Column(db.Integer, primary_key=True)
    section = db.Column(db.String(50))
    remarks_file_no = db.Column(db.String(100))
    pen = db.Column(db.String(50))
    prefix = db.Column(db.String(20))
    name = db.Column(db.String(200))
    designation = db.Column(db.String(100))
    institution = db.Column(db.String(200))
    status = db.Column(db.String(50))  # Clear / Not Clear
    created_at = db.Column(db.String(50))  # TEXT in desktop database
    
    def __repr__(self):
        return f'<RemarksEntry {self.pen} - {self.status}>'


class CustomCategory(db.Model):
    """Custom categories model."""
    __tablename__ = 'custom_categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    is_active = db.Column(db.Integer, default=1)  # INTEGER in desktop database
    has_link = db.Column(db.Integer, default=0)  # INTEGER in desktop database
    created_date = db.Column(db.String(50))  # TEXT in desktop database
    
    def __repr__(self):
        return f'<CustomCategory {self.name}>'


class CustomFileType(db.Model):
    """Custom file types model."""
    __tablename__ = 'custom_file_types'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    is_active = db.Column(db.Integer, default=1)  # INTEGER in desktop database
    has_link = db.Column(db.Integer, default=0)  # INTEGER in desktop database
    created_date = db.Column(db.String(50))  # TEXT in desktop database
    
    def __repr__(self):
        return f'<CustomFileType {self.name}>'


class CMOPortalDetails(db.Model):
    """CMO Portal details model."""
    __tablename__ = 'cmo_portal_details'
    
    id = db.Column(db.Integer, primary_key=True)
    file_number = db.Column(db.String(100), db.ForeignKey('files.file_number'), unique=True, nullable=False)
    docket_number = db.Column(db.String(100))
    date_of_receipt = db.Column(db.String(20))
    finalised = db.Column(db.String(10))
    finalised_date = db.Column(db.String(20))
    
    def __repr__(self):
        return f'<CMOPortalDetails {self.file_number}>'


class RVUDetails(db.Model):
    """RVU details model."""
    __tablename__ = 'rvu_details'
    
    id = db.Column(db.Integer, primary_key=True)
    file_number = db.Column(db.String(100), db.ForeignKey('files.file_number'), unique=True, nullable=False)
    dhs_file_number = db.Column(db.String(100))
    receipt_date = db.Column(db.String(20))
    receipt_date_inquiry_status = db.Column(db.String(50))
    receipt_date_inquiry_date = db.Column(db.String(20))
    report_status = db.Column(db.String(50))
    interim_report_date = db.Column(db.String(20))
    sent_date = db.Column(db.String(20))
    
    def __repr__(self):
        return f'<RVUDetails {self.file_number}>'


class TraceDetails(db.Model):
    """Physical file trace details model."""
    __tablename__ = 'trace_details'
    
    id = db.Column(db.Integer, primary_key=True)
    file_number = db.Column(db.String(100), db.ForeignKey('files.file_number'), unique=True, nullable=False)
    almirah = db.Column(db.String(50))
    rack = db.Column(db.String(20))
    row = db.Column(db.String(20))
    migrated_to_eoffice = db.Column(db.String(10))
    eoffice_file_number = db.Column(db.String(100))
    
    def __repr__(self):
        return f'<TraceDetails {self.file_number}>'


# ============================================================================
# ADDITIONAL MODELS - Matching Desktop Database Schema
# ============================================================================

class InstitutionCategory(db.Model):
    """Institution categories model."""
    __tablename__ = 'institution_categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    
    def __repr__(self):
        return f'<InstitutionCategory {self.name}>'


class KESCPCRDetails(db.Model):
    """KESCPCR (Kerala State Commission for Protection of Child Rights) details model."""
    __tablename__ = 'kescpcr_details'
    
    id = db.Column(db.Integer, primary_key=True)
    file_number = db.Column(db.String(100), db.ForeignKey('files.file_number'), nullable=False)
    kescpcr_case_no = db.Column(db.String(100))
    receipt_date = db.Column(db.String(20))
    report_status = db.Column(db.String(50))
    interim_report_date = db.Column(db.String(20))
    sent_date = db.Column(db.String(20))
    finalised = db.Column(db.String(10))
    finalised_date = db.Column(db.String(20))
    
    def __repr__(self):
        return f'<KESCPCRDetails {self.file_number}>'


class KHRCDetails(db.Model):
    """KHRC (Kerala Human Rights Commission) details model."""
    __tablename__ = 'khrc_details'
    
    id = db.Column(db.Integer, primary_key=True)
    file_number = db.Column(db.String(100), db.ForeignKey('files.file_number'), nullable=False)
    khrc_case_no = db.Column(db.String(100))
    receipt_date = db.Column(db.String(20))
    report_status = db.Column(db.String(50))
    interim_report_date = db.Column(db.String(20))
    sent_date = db.Column(db.String(20))
    finalised = db.Column(db.String(10))
    finalised_date = db.Column(db.String(20))
    
    def __repr__(self):
        return f'<KHRCDetails {self.file_number}>'


class SCSTDetails(db.Model):
    """SC/ST details model."""
    __tablename__ = 'scst_details'
    
    id = db.Column(db.Integer, primary_key=True)
    file_number = db.Column(db.String(100), db.ForeignKey('files.file_number'), nullable=False)
    scst_case_no = db.Column(db.String(100))
    receipt_date = db.Column(db.String(20))
    report_status = db.Column(db.String(50))
    interim_report_date = db.Column(db.String(20))
    sent_date = db.Column(db.String(20))
    finalised = db.Column(db.String(10))
    finalised_date = db.Column(db.String(20))
    
    def __repr__(self):
        return f'<SCSTDetails {self.file_number}>'


class KWCDetails(db.Model):
    """KWC (Kerala Women Commission) details model."""
    __tablename__ = 'kwc_details'
    
    id = db.Column(db.Integer, primary_key=True)
    file_number = db.Column(db.String(100), db.ForeignKey('files.file_number'), nullable=False)
    kwc_case_no = db.Column(db.String(100))
    receipt_date = db.Column(db.String(20))
    report_status = db.Column(db.String(50))
    interim_report_date = db.Column(db.String(20))
    sent_date = db.Column(db.String(20))
    finalised = db.Column(db.String(10))
    finalised_date = db.Column(db.String(20))
    
    def __repr__(self):
        return f'<KWCDetails {self.file_number}>'


class VigilanceACDetails(db.Model):
    """Vigilance AC details model."""
    __tablename__ = 'vigilance_ac_details'
    
    id = db.Column(db.Integer, primary_key=True)
    file_number = db.Column(db.String(100), db.ForeignKey('files.file_number'), nullable=False)
    vigilance_ac_case_no = db.Column(db.String(100))
    receipt_date = db.Column(db.String(20))
    finalised = db.Column(db.String(10))
    finalised_date = db.Column(db.String(20))
    
    def __repr__(self):
        return f'<VigilanceACDetails {self.file_number}>'


class RajyaLokNiyamasabhaDetails(db.Model):
    """Rajya Lok Niyamasabha details model."""
    __tablename__ = 'rajya_lok_niyamasabha_details'
    
    id = db.Column(db.Integer, primary_key=True)
    file_number = db.Column(db.String(100), db.ForeignKey('files.file_number'), nullable=False)
    sabha_type = db.Column(db.String(50))
    receipt_date = db.Column(db.String(20))
    report_status = db.Column(db.String(50))
    sent_date = db.Column(db.String(20))
    finalised = db.Column(db.String(10))
    finalised_date = db.Column(db.String(20))
    
    def __repr__(self):
        return f'<RajyaLokNiyamasabhaDetails {self.file_number}>'


class PoliceCaseDetails(db.Model):
    """Police case details model."""
    __tablename__ = 'police_case_details'
    
    id = db.Column(db.Integer, primary_key=True)
    file_number = db.Column(db.String(100), db.ForeignKey('files.file_number'), nullable=False)
    case_no = db.Column(db.String(100))
    fir_no = db.Column(db.String(100))
    case_date = db.Column(db.String(20))
    police_station = db.Column(db.String(200))
    detained_over_48_hours = db.Column(db.String(10))
    suspended_from_service = db.Column(db.String(10))
    present_status = db.Column(db.String(100))
    finalised = db.Column(db.String(10))
    finalised_date = db.Column(db.String(20))
    
    def __repr__(self):
        return f'<PoliceCaseDetails {self.file_number}>'


class AttackOnDoctorsCase(db.Model):
    """Attack on doctors case model."""
    __tablename__ = 'attack_on_doctors_cases'
    
    id = db.Column(db.Integer, primary_key=True)
    file_number = db.Column(db.String(100), db.ForeignKey('files.file_number'), nullable=False)
    police_informed = db.Column(db.String(10))
    police_station = db.Column(db.String(200))
    reported_date = db.Column(db.String(20))
    
    attacked_doctors = db.relationship('AttackedDoctor', backref='case', lazy='dynamic', cascade='all, delete-orphan')
    culprits = db.relationship('Culprit', backref='case', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<AttackOnDoctorsCase {self.file_number}>'


class AttackedDoctor(db.Model):
    """Attacked doctors model."""
    __tablename__ = 'attacked_doctors'
    
    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.Integer, db.ForeignKey('attack_on_doctors_cases.id'))
    pen = db.Column(db.String(50))
    name = db.Column(db.String(200))
    designation = db.Column(db.String(100))
    institution = db.Column(db.String(200))
    
    def __repr__(self):
        return f'<AttackedDoctor {self.name}>'


class Culprit(db.Model):
    """Culprits model (for attack on doctors cases)."""
    __tablename__ = 'culprits'
    
    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.Integer, db.ForeignKey('attack_on_doctors_cases.id'))
    culprit_name = db.Column(db.String(200))
    culprit_address = db.Column(db.Text)
    
    def __repr__(self):
        return f'<Culprit {self.culprit_name}>'


class AttackOnStaffsCase(db.Model):
    """Attack on staffs case model."""
    __tablename__ = 'attack_on_staffs_cases'
    
    id = db.Column(db.Integer, primary_key=True)
    file_number = db.Column(db.String(100), db.ForeignKey('files.file_number'), nullable=False)
    police_informed = db.Column(db.String(10))
    police_station = db.Column(db.String(200))
    reported_date = db.Column(db.String(20))
    
    attacked_staffs = db.relationship('AttackedStaff', backref='case', lazy='dynamic', cascade='all, delete-orphan')
    culprits = db.relationship('CulpritStaff', backref='case', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<AttackOnStaffsCase {self.file_number}>'


class AttackedStaff(db.Model):
    """Attacked staffs model."""
    __tablename__ = 'attacked_staffs'
    
    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.Integer, db.ForeignKey('attack_on_staffs_cases.id'))
    pen = db.Column(db.String(50))
    name = db.Column(db.String(200))
    designation = db.Column(db.String(100))
    institution = db.Column(db.String(200))
    
    def __repr__(self):
        return f'<AttackedStaff {self.name}>'


class CulpritStaff(db.Model):
    """Culprits model (for attack on staffs cases)."""
    __tablename__ = 'culprits_staffs'
    
    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.Integer, db.ForeignKey('attack_on_staffs_cases.id'))
    culprit_name = db.Column(db.String(200))
    culprit_address = db.Column(db.Text)
    
    def __repr__(self):
        return f'<CulpritStaff {self.culprit_name}>'


class FileMigration(db.Model):
    """File migration model."""
    __tablename__ = 'file_migrations'
    
    id = db.Column(db.Integer, primary_key=True)
    physical_file_number = db.Column(db.String(100))
    eoffice_file_number = db.Column(db.String(100))
    migration_date = db.Column(db.String(20))
    created_date = db.Column(db.String(50))
    
    def __repr__(self):
        return f'<FileMigration {self.physical_file_number}>'


class Communication(db.Model):
    """Communications model."""
    __tablename__ = 'communications'
    
    id = db.Column(db.Integer, primary_key=True)
    file_number = db.Column(db.String(100), db.ForeignKey('files.file_number'), nullable=False)
    document_type = db.Column(db.String(100))
    document_title = db.Column(db.String(200))
    malayalam_content = db.Column(db.Text)
    english_summary = db.Column(db.Text)
    document_path = db.Column(db.String(500))
    temp_path = db.Column(db.String(500))
    created_date = db.Column(db.String(50))
    created_by = db.Column(db.String(100))
    last_modified = db.Column(db.String(50))
    document_format = db.Column(db.String(50))
    status = db.Column(db.String(50))
    doc_metadata = db.Column('metadata', db.Text)  # 'metadata' is reserved in SQLAlchemy
    communication_name = db.Column(db.String(200))
    content = db.Column(db.Text)
    modified_date = db.Column(db.String(50))
    
    def __repr__(self):
        return f'<Communication {self.file_number} - {self.document_title}>'


class PreliminaryStatement(db.Model):
    """Preliminary statement model."""
    __tablename__ = 'preliminary_statements'
    
    file_number = db.Column(db.String(100), db.ForeignKey('files.file_number'), primary_key=True)
    basic_info = db.Column(db.Text)
    respondents = db.Column(db.Text)
    qa_pairs = db.Column(db.Text)
    created_date = db.Column(db.String(50))
    last_modified = db.Column(db.String(50))
    
    def __repr__(self):
        return f'<PreliminaryStatement {self.file_number}>'


class Rule15Statement(db.Model):
    """Rule 15 statement model."""
    __tablename__ = 'rule15_statements'
    
    file_number = db.Column(db.String(100), db.ForeignKey('files.file_number'), primary_key=True)
    basic_info = db.Column(db.Text)
    respondents = db.Column(db.Text)
    qa_pairs = db.Column(db.Text)
    created_date = db.Column(db.String(50))
    last_modified = db.Column(db.String(50))
    
    def __repr__(self):
        return f'<Rule15Statement {self.file_number}>'
