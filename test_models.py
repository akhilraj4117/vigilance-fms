import sys
sys.path.insert(0, '.')
from app import app
print('App created successfully!')
print('Testing model imports...')
from models import (
    User, File, Institution, Employee, DisciplinaryAction, 
    UnauthorisedAbsentee, PREntry, RTIApplication, RTIAppeal,
    CourtCase, InquiryDetails, WomenHarassmentCase, 
    WHEmployeeInvolved, WHCulpritInvolved, ComplaintDetails,
    ReportSoughtDetails, ReportAskedDetails, SocialSecurityPension,
    RemarksEntry, CustomCategory, CustomFileType, CMOPortalDetails,
    RVUDetails, TraceDetails, InstitutionCategory, KESCPCRDetails,
    KHRCDetails, SCSTDetails, KWCDetails, VigilanceACDetails,
    RajyaLokNiyamasabhaDetails, PoliceCaseDetails, AttackOnDoctorsCase,
    AttackedDoctor, Culprit, AttackOnStaffsCase, AttackedStaff,
    CulpritStaff, FileMigration, Communication, PreliminaryStatement,
    Rule15Statement
)
print('All models imported successfully!')

# Count records in database for verification
with app.app_context():
    from extensions import db
    print(f"\n--- Database Record Counts ---")
    print(f"Files: {File.query.count()}")
    print(f"Institutions: {Institution.query.count()}")
    print(f"Employees: {Employee.query.count()}")
    print(f"Disciplinary Actions: {DisciplinaryAction.query.count()}")
    print(f"RTI Applications: {RTIApplication.query.count()}")
    print(f"Court Cases: {CourtCase.query.count()}")
    print(f"Women Harassment Cases: {WomenHarassmentCase.query.count()}")
    print(f"Custom Categories: {CustomCategory.query.count()}")
    print(f"Custom File Types: {CustomFileType.query.count()}")
    print(f"Communications: {Communication.query.count()}")
