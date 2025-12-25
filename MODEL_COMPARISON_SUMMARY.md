# Web App vs Desktop App - Model Comparison Summary

## Overview
This document summarizes the comparison between the Desktop App (FileMgtN2.0.py) and the Web App database models, and the changes made to ensure exact parity.

## Database Tables Comparison

### Tables in Desktop Database (43 tables)
The desktop database (vigilance_files.db) contains the following tables:

| Table Name | Web App Status | Notes |
|------------|----------------|-------|
| attack_on_doctors_cases | ✅ Added | AttackOnDoctorsCase model |
| attack_on_staffs_cases | ✅ Added | AttackOnStaffsCase model |
| attacked_doctors | ✅ Added | AttackedDoctor model |
| attacked_staffs | ✅ Added | AttackedStaff model |
| cmo_portal_details | ✅ Exists | CMOPortalDetails model |
| communications | ✅ Added | Communication model |
| complaint_details | ✅ Exists | ComplaintDetails model |
| court_case_details | ✅ Exists | CourtCase model |
| culprits | ✅ Added | Culprit model |
| culprits_staffs | ✅ Added | CulpritStaff model |
| custom_categories | ✅ Fixed | Column types updated |
| custom_file_types | ✅ Fixed | Column types updated |
| disciplinary_action_details | ✅ Exists | DisciplinaryAction model |
| employees | ✅ Exists | Exact schema match |
| file_migrations | ✅ Added | FileMigration model |
| files | ✅ Exists | Exact schema match |
| inquiry_details | ✅ Exists | InquiryDetails model |
| institution_categories | ✅ Added | InstitutionCategory model |
| institutions | ✅ Exists | Exact schema match |
| kescpcr_details | ✅ Added | KESCPCRDetails model |
| khrc_details | ✅ Added | KHRCDetails model |
| kwc_details | ✅ Added | KWCDetails model |
| police_case_details | ✅ Added | PoliceCaseDetails model |
| pr_entries | ✅ Exists | PREntry model |
| preliminary_statements | ✅ Added | PreliminaryStatement model |
| rajya_lok_niyamasabha_details | ✅ Added | RajyaLokNiyamasabhaDetails model |
| remarks_entries | ✅ Fixed | created_at changed to TEXT |
| report_asked_details | ✅ Exists | ReportAskedDetails model |
| report_sought_details | ✅ Exists | ReportSoughtDetails model |
| rti_appeals | ✅ Exists | RTIAppeal model |
| rti_applications | ✅ Exists | RTIApplication model |
| rule15_statements | ✅ Added | Rule15Statement model |
| rvu_details | ✅ Exists | RVUDetails model |
| scst_details | ✅ Added | SCSTDetails model |
| social_security_pension_details | ✅ Exists | SocialSecurityPension model |
| trace_details | ✅ Exists | TraceDetails model |
| unauthorised_absentees | ✅ Exists | UnauthorisedAbsentee model |
| users | ✅ Exists | User model |
| vigilance_ac_details | ✅ Added | VigilanceACDetails model |
| wh_culprits_involved | ✅ Exists | WHCulpritInvolved model |
| wh_employees_involved | ✅ Exists | WHEmployeeInvolved model |
| women_harassment_cases | ✅ Exists | WomenHarassmentCase model |
| sqlite_sequence | N/A | SQLite internal table |

## New Models Added (18 models)

1. **InstitutionCategory** - Institution categories table
2. **KESCPCRDetails** - Kerala State Commission for Protection of Child Rights
3. **KHRCDetails** - Kerala Human Rights Commission
4. **SCSTDetails** - SC/ST Commission details
5. **KWCDetails** - Kerala Women Commission
6. **VigilanceACDetails** - Vigilance Anti-Corruption details
7. **RajyaLokNiyamasabhaDetails** - State Legislature/Parliament details
8. **PoliceCaseDetails** - Police case details
9. **AttackOnDoctorsCase** - Attack on doctors case
10. **AttackedDoctor** - Attacked doctors record
11. **Culprit** - Culprits in doctor attack cases
12. **AttackOnStaffsCase** - Attack on staff case
13. **AttackedStaff** - Attacked staff record
14. **CulpritStaff** - Culprits in staff attack cases
15. **FileMigration** - File migration tracking
16. **Communication** - Communications/Documents
17. **PreliminaryStatement** - Preliminary inquiry statements
18. **Rule15Statement** - Rule 15 inquiry statements

## Column Type Fixes

### RemarksEntry
- `created_at`: Changed from `DateTime` to `String(50)` (TEXT in desktop)

### CustomCategory
- `is_active`: Changed from `Boolean` to `Integer` (INTEGER in desktop)
- `has_link`: Changed from `Boolean` to `Integer` (INTEGER in desktop)
- `created_date`: Changed from `DateTime` to `String(50)` (TEXT in desktop)

### CustomFileType
- `is_active`: Changed from `Boolean` to `Integer` (INTEGER in desktop)
- `has_link`: Changed from `Boolean` to `Integer` (INTEGER in desktop)
- `created_date`: Changed from `DateTime` to `String(50)` (TEXT in desktop)

### Communication
- `metadata`: Renamed to `doc_metadata` (Python attribute) mapping to `metadata` column (reserved name in SQLAlchemy)

## Existing Models - Schema Verification

The following models were verified to match the desktop database schema exactly:

| Model | Primary Key | Matches Desktop |
|-------|-------------|-----------------|
| File | file_number (TEXT) | ✅ Yes |
| Institution | id (INTEGER) | ✅ Yes |
| Employee | pen (TEXT) | ✅ Yes |
| DisciplinaryAction | id (INTEGER) | ✅ Yes |
| UnauthorisedAbsentee | id (INTEGER) | ✅ Yes |
| PREntry | id (INTEGER) | ✅ Yes |
| RTIApplication | id (INTEGER) | ✅ Yes |
| RTIAppeal | id (INTEGER) | ✅ Yes |
| CourtCase | id (INTEGER) | ✅ Yes |
| InquiryDetails | id (INTEGER) | ✅ Yes |
| WomenHarassmentCase | id (INTEGER) | ✅ Yes |
| WHEmployeeInvolved | id (INTEGER) | ✅ Yes |
| WHCulpritInvolved | id (INTEGER) | ✅ Yes |
| ComplaintDetails | id (INTEGER) | ✅ Yes |
| ReportSoughtDetails | id (INTEGER) | ✅ Yes |
| ReportAskedDetails | id (INTEGER) | ✅ Yes |
| SocialSecurityPension | id (INTEGER) | ✅ Yes |
| CMOPortalDetails | id (INTEGER) | ✅ Yes |
| RVUDetails | id (INTEGER) | ✅ Yes |
| TraceDetails | id (INTEGER) | ✅ Yes |

## Database Record Counts (Current)

- Files: 1080
- Institutions: 128
- Employees: 6497
- Disciplinary Actions: 127
- RTI Applications: 21
- Court Cases: 1
- Women Harassment Cases: 2
- Custom Categories: 0
- Custom File Types: 8
- Communications: 167

## Web App Status

✅ Flask app starts successfully
✅ All models can be imported
✅ Database connection works
✅ All routes functional

## Files Modified

1. `Web App Files/models.py` - Updated with 18 new models and column type fixes

## Date

Comparison completed: $(date)
