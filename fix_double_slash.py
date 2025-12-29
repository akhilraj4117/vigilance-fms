"""
Script to fix file numbers with double slashes in the database.
This will replace // with / in all file numbers.
"""
from app import app, db
from models import File, PREntry, DisciplinaryAction, InquiryDetails, TraceDetails
from models import ReportSoughtDetails, ReportAskedDetails, CourtCase, RTIApplication
from models import SocialSecurityPension, ComplaintDetails, CMOPortalDetails, RVUDetails
from models import KESCPCRDetails, KHRCDetails, SCSTDetails, KWCDetails, VigilanceACDetails
from models import RajyaLokNiyamasabhaDetails, PoliceCaseDetails, AttackOnDoctorsCase
from models import AttackOnStaffsCase, WomenHarassmentCase

def fix_double_slashes():
    """Fix double slashes in file numbers across all tables."""
    
    with app.app_context():
        # Get all file numbers with double slashes
        files_with_double_slash = File.query.filter(File.file_number.like('%//%')).all()
        
        if not files_with_double_slash:
            print("No files with double slashes found.")
            return
        
        print(f"Found {len(files_with_double_slash)} files with double slashes:")
        
        for file in files_with_double_slash:
            old_file_number = file.file_number
            new_file_number = old_file_number.replace('//', '/')
            
            print(f"\nFixing: {old_file_number} -> {new_file_number}")
            
            # Update the file itself
            file.file_number = new_file_number
            
            # Update all related records
            # PR Entries
            pr_entries = PREntry.query.filter_by(file_number=old_file_number).all()
            for pr in pr_entries:
                pr.file_number = new_file_number
            print(f"  Updated {len(pr_entries)} PR entries")
            
            # Disciplinary Actions
            da_records = DisciplinaryAction.query.filter_by(file_number=old_file_number).all()
            for da in da_records:
                da.file_number = new_file_number
            print(f"  Updated {len(da_records)} disciplinary actions")
            
            # Inquiry Details
            inquiries = InquiryDetails.query.filter_by(file_number=old_file_number).all()
            for inquiry in inquiries:
                inquiry.file_number = new_file_number
            print(f"  Updated {len(inquiries)} inquiry details")
            
            # Trace Details
            traces = TraceDetails.query.filter_by(file_number=old_file_number).all()
            for trace in traces:
                trace.file_number = new_file_number
            print(f"  Updated {len(traces)} trace details")
            
            # Report Sought
            reports_sought = ReportSoughtDetails.query.filter_by(file_number=old_file_number).all()
            for report in reports_sought:
                report.file_number = new_file_number
            print(f"  Updated {len(reports_sought)} report sought records")
            
            # Report Asked
            reports_asked = ReportAskedDetails.query.filter_by(file_number=old_file_number).all()
            for report in reports_asked:
                report.file_number = new_file_number
            print(f"  Updated {len(reports_asked)} report asked records")
            
            # RTI Applications
            rti_apps = RTIApplication.query.filter_by(file_number=old_file_number).all()
            for rti in rti_apps:
                rti.file_number = new_file_number
            print(f"  Updated {len(rti_apps)} RTI applications")
            
            # Court Cases
            court_cases = CourtCase.query.filter_by(file_number=old_file_number).all()
            for case in court_cases:
                case.file_number = new_file_number
            print(f"  Updated {len(court_cases)} court cases")
            
            # Social Security Pension
            ssp_records = SocialSecurityPension.query.filter_by(file_number=old_file_number).all()
            for ssp in ssp_records:
                ssp.file_number = new_file_number
            print(f"  Updated {len(ssp_records)} SSP records")
            
            # Complaints
            complaints = ComplaintDetails.query.filter_by(file_number=old_file_number).all()
            for complaint in complaints:
                complaint.file_number = new_file_number
            print(f"  Updated {len(complaints)} complaints")
            
            # CMO Portal
            cmo_records = CMOPortalDetails.query.filter_by(file_number=old_file_number).all()
            for cmo in cmo_records:
                cmo.file_number = new_file_number
            print(f"  Updated {len(cmo_records)} CMO portal records")
            
            # RVU
            rvu_records = RVUDetails.query.filter_by(file_number=old_file_number).all()
            for rvu in rvu_records:
                rvu.file_number = new_file_number
            print(f"  Updated {len(rvu_records)} RVU records")
            
            # Women Harassment
            wh_cases = WomenHarassmentCase.query.filter_by(file_number=old_file_number).all()
            for wh in wh_cases:
                wh.file_number = new_file_number
            print(f"  Updated {len(wh_cases)} women harassment cases")
            
            # Other case types
            police_cases = PoliceCaseDetails.query.filter_by(file_number=old_file_number).all()
            for pc in police_cases:
                pc.file_number = new_file_number
            print(f"  Updated {len(police_cases)} police cases")
            
            attack_doctors = AttackOnDoctorsCase.query.filter_by(file_number=old_file_number).all()
            for ad in attack_doctors:
                ad.file_number = new_file_number
            print(f"  Updated {len(attack_doctors)} attack on doctors cases")
            
            attack_staffs = AttackOnStaffsCase.query.filter_by(file_number=old_file_number).all()
            for ast in attack_staffs:
                ast.file_number = new_file_number
            print(f"  Updated {len(attack_staffs)} attack on staffs cases")
        
        # Commit all changes
        db.session.commit()
        print(f"\n✅ Successfully fixed {len(files_with_double_slash)} files!")
        
        # Show summary
        print("\nFixed file numbers:")
        for file in files_with_double_slash:
            print(f"  ✓ {file.file_number}")

if __name__ == '__main__':
    fix_double_slashes()
