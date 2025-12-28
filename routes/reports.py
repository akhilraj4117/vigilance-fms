"""
Report generation routes for the Flask application.
"""
from flask import Blueprint, render_template, request, Response, redirect, url_for, jsonify
from flask_login import login_required
from models import (
    File, DisciplinaryAction, UnauthorisedAbsentee, RTIApplication, 
    CourtCase, InquiryDetails, WomenHarassmentCase, SocialSecurityPension, Employee
)
from extensions import db
from sqlalchemy import func, or_, and_, case, distinct
import csv
import io
from datetime import datetime

reports_bp = Blueprint('reports', __name__)


@reports_bp.route('/followup-redirect')
@login_required
def followup_redirect():
    """Redirect to follow-up files - this is a main tab."""
    return redirect(url_for('file_movements.follow_up_files'))


@reports_bp.route('/')
@login_required
def index():
    """Reports and Statistics dashboard - matching desktop app."""
    tab = request.args.get('tab', 'file_status')
    subtab = request.args.get('subtab', 'eoffice_physical')
    year = request.args.get('year', '')
    
    # Only load statistics needed for the current tab (lazy loading)
    stats = get_tab_statistics(tab, subtab)
    
    # Get available years for DA Overview (only if needed)
    years = []
    da_monthly_stats = {}
    
    if tab == 'da_overview':
        years = get_da_years()
        if not year and years and years[0] != 'No data':
            year = years[-1]  # Default to most recent year
        
        # Get DA monthly stats if year is selected
        if year and year != 'No data':
            da_monthly_stats = get_da_monthly_stats(year)
    
    return render_template('reports/index.html',
                          tab=tab,
                          subtab=subtab,
                          stats=stats,
                          years=years,
                          selected_year=year,
                          da_monthly_stats=da_monthly_stats)


def get_tab_statistics(tab, subtab):
    """Get statistics only for the requested tab (lazy loading for performance)."""
    stats = {}
    
    try:
        if tab == 'file_status':
            # Load only file status related stats
            if subtab == 'eoffice_physical':
                stats['eoffice_physical'] = get_file_type_counts_by_status()
            elif subtab == 'status_distribution':
                stats['status_distribution'] = get_status_distribution()
            elif subtab == 'da_files':
                stats['da_files'] = get_da_files_counts()
            elif subtab == 'category_status':
                stats['category_by_status'] = get_category_counts_by_status()
            elif subtab == 'type_status':
                stats['type_by_status'] = get_type_counts_by_status()
            else:
                # Default: load basic stats
                stats['eoffice_physical'] = get_file_type_counts_by_status()
                
        elif tab == 'categories':
            stats['categories'] = get_category_distribution()
            
        elif tab == 'file_types':
            stats['file_types'] = get_file_type_distribution()
            
        elif tab == 'institution_types':
            stats['institution_types'] = get_institution_type_counts()
            
        elif tab == 'files_by_year':
            stats['files_by_year'] = get_files_by_year()
            
        elif tab == 'ua_stats':
            stats['ua_stats'] = get_ua_statistics()
            
        elif tab == 'related_employees':
            stats['related_employees'] = get_related_employees()
            
        elif tab == 'da_overview':
            # DA overview stats are loaded separately
            pass
            
    except Exception as e:
        print(f"Error getting statistics for tab {tab}: {e}")
    
    return stats


def get_all_statistics():
    """Get all statistics data for the reports tab."""
    stats = {}
    
    try:
        # 1. E-Office / Physical Files counts by status
        stats['eoffice_physical'] = get_file_type_counts_by_status()
        
        # 2. Status Distribution
        stats['status_distribution'] = get_status_distribution()
        
        # 3. Files with Disciplinary Action
        stats['da_files'] = get_da_files_counts()
        
        # 4. Category Distribution (by status)
        stats['category_by_status'] = get_category_counts_by_status()
        
        # 5. Type of File Distribution (by status)
        stats['type_by_status'] = get_type_counts_by_status()
        
        # 6. Category Distribution (simple)
        stats['categories'] = get_category_distribution()
        
        # 7. File Types (simple)
        stats['file_types'] = get_file_type_distribution()
        
        # 8. Institution Types
        stats['institution_types'] = get_institution_type_counts()
        
        # 9. Files by Year
        stats['files_by_year'] = get_files_by_year()
        
        # 10. Unauthorised Absence Statistics
        stats['ua_stats'] = get_ua_statistics()
        
        # 11. Related Employees
        stats['related_employees'] = get_related_employees()
        
    except Exception as e:
        print(f"Error getting statistics: {e}")
    
    return stats


def get_file_type_counts_by_status():
    """Get E-Office and Physical file counts by Active/Closed status using is_closed field."""
    result = {}
    
    try:
        # Use raw SQL to match desktop app logic exactly
        # E-Office files
        eoffice_active_res = db.session.execute(db.text("""
            SELECT COUNT(*) FROM files
            WHERE file_type = 'E-Office' AND is_closed = 0 AND (status != 'Handed Over' OR status IS NULL)
        """))
        eoffice_active = eoffice_active_res.scalar() or 0
        
        eoffice_closed_res = db.session.execute(db.text("""
            SELECT COUNT(*) FROM files
            WHERE file_type = 'E-Office' AND (is_closed = 1 OR status = 'Handed Over')
        """))
        eoffice_closed = eoffice_closed_res.scalar() or 0
        
        result['E-Office'] = {'Active': eoffice_active, 'Closed': eoffice_closed, 'Total': eoffice_active + eoffice_closed}
        
        # Physical files
        physical_active_res = db.session.execute(db.text("""
            SELECT COUNT(*) FROM files
            WHERE file_type = 'Physical' AND is_closed = 0 AND (status != 'Handed Over' OR status IS NULL)
        """))
        physical_active = physical_active_res.scalar() or 0
        
        physical_closed_res = db.session.execute(db.text("""
            SELECT COUNT(*) FROM files
            WHERE file_type = 'Physical' AND (is_closed = 1 OR status = 'Handed Over')
        """))
        physical_closed = physical_closed_res.scalar() or 0
        
        result['Physical'] = {'Active': physical_active, 'Closed': physical_closed, 'Total': physical_active + physical_closed}
        
        # Total
        total_active = eoffice_active + physical_active
        total_closed = eoffice_closed + physical_closed
        result['Total'] = {'Active': total_active, 'Closed': total_closed, 'Total': total_active + total_closed}
        
    except Exception as e:
        print(f"Error getting file type counts: {e}")
        result = {
            'E-Office': {'Active': 0, 'Closed': 0, 'Total': 0},
            'Physical': {'Active': 0, 'Closed': 0, 'Total': 0},
            'Total': {'Active': 0, 'Closed': 0, 'Total': 0}
        }
    
    return result


def get_status_distribution():
    """Get file count by status."""
    result = db.session.query(
        File.status, func.count(File.file_number)
    ).group_by(File.status).all()
    
    return {(s or 'Unknown'): c for s, c in result}


def get_da_files_counts():
    """Get files with disciplinary action counts by status using is_closed field."""
    try:
        # Use raw SQL to match desktop app logic exactly
        active_res = db.session.execute(db.text("""
            SELECT COUNT(*) FROM files
            WHERE disciplinary_action = 'Yes' AND is_closed = 0 AND (status != 'Handed Over' OR status IS NULL)
        """))
        active = active_res.scalar() or 0
        
        closed_res = db.session.execute(db.text("""
            SELECT COUNT(*) FROM files
            WHERE disciplinary_action = 'Yes' AND (is_closed = 1 OR status = 'Handed Over')
        """))
        closed = closed_res.scalar() or 0
        
        return {'Active': active, 'Closed': closed, 'Total': active + closed}
    except Exception as e:
        print(f"Error getting DA files counts: {e}")
        return {'Active': 0, 'Closed': 0, 'Total': 0}


def get_category_counts_by_status():
    """Get category counts with Active/Closed breakdown - unpacks JSON arrays like desktop app."""
    import json
    result = {}
    
    try:
        # Get all files with their category and status
        rows = db.session.execute(db.text("""
            SELECT category, is_closed, status FROM files 
            WHERE category IS NOT NULL AND category != ''
        """)).fetchall()
        
        for row in rows:
            category_str = row[0]
            is_closed = row[1]
            status = row[2]
            
            try:
                # Try to parse as JSON array
                categories = json.loads(category_str) if category_str else []
                if isinstance(categories, str):
                    categories = [categories]
                elif not isinstance(categories, list):
                    categories = []
            except json.JSONDecodeError:
                categories = [category_str] if category_str else []
            
            for cat in categories:
                if isinstance(cat, str) and cat.strip():
                    if cat not in result:
                        result[cat] = {'Active': 0, 'Closed': 0, 'Total': 0}
                    
                    if is_closed == 0 and status != 'Handed Over':
                        result[cat]['Active'] += 1
                    else:
                        result[cat]['Closed'] += 1
                    result[cat]['Total'] += 1
    except Exception as e:
        print(f"Error getting category counts: {e}")
    
    return result


def get_type_counts_by_status():
    """Get type of file counts with Active/Closed breakdown - unpacks JSON arrays like desktop app."""
    import json
    result = {}
    
    try:
        # Get all files with their type_of_file and status
        rows = db.session.execute(db.text("""
            SELECT type_of_file, is_closed, status FROM files 
            WHERE type_of_file IS NOT NULL AND type_of_file != ''
        """)).fetchall()
        
        for row in rows:
            type_str = row[0]
            is_closed = row[1]
            status = row[2]
            
            try:
                # Try to parse as JSON array
                file_types = json.loads(type_str) if type_str else []
                if isinstance(file_types, str):
                    file_types = [file_types]
                elif not isinstance(file_types, list):
                    file_types = []
            except json.JSONDecodeError:
                file_types = [type_str] if type_str else []
            
            for ft in file_types:
                if isinstance(ft, str) and ft.strip():
                    if ft not in result:
                        result[ft] = {'Active': 0, 'Closed': 0, 'Total': 0}
                    
                    if is_closed == 0 and status != 'Handed Over':
                        result[ft]['Active'] += 1
                    else:
                        result[ft]['Closed'] += 1
                    result[ft]['Total'] += 1
    except Exception as e:
        print(f"Error getting type counts: {e}")
    
    return result


def get_category_distribution():
    """Get simple category distribution - unpacks JSON arrays like desktop app."""
    import json
    counts = {}
    
    try:
        # Get all category values
        result = db.session.execute(db.text("SELECT category FROM files WHERE category IS NOT NULL AND category != ''"))
        for row in result:
            category_str = row[0]
            try:
                # Try to parse as JSON array
                categories = json.loads(category_str) if category_str else []
                # Handle case where categories is a string instead of a list
                if isinstance(categories, str):
                    categories = [categories]
                elif not isinstance(categories, list):
                    categories = []
            except json.JSONDecodeError:
                # Handle malformed JSON - treat as single category string
                categories = [category_str] if category_str else []
            
            for cat in categories:
                if isinstance(cat, str) and cat.strip():  # Only count non-empty string categories
                    counts[cat] = counts.get(cat, 0) + 1
    except Exception as e:
        print(f"Error getting category distribution: {e}")
    
    return counts


def get_file_type_distribution():
    """Get simple file type distribution - unpacks JSON arrays like desktop app."""
    import json
    counts = {}
    
    try:
        # Get all type_of_file values
        result = db.session.execute(db.text("SELECT type_of_file FROM files WHERE type_of_file IS NOT NULL AND type_of_file != ''"))
        for row in result:
            type_str = row[0]
            try:
                # Try to parse as JSON array
                file_types = json.loads(type_str) if type_str else []
                # Handle case where file_types is a string instead of a list
                if isinstance(file_types, str):
                    file_types = [file_types]
                elif not isinstance(file_types, list):
                    file_types = []
            except json.JSONDecodeError:
                # Handle malformed JSON - treat as single type string
                file_types = [type_str] if type_str else []
            
            for ft in file_types:
                if isinstance(ft, str) and ft.strip():  # Only count non-empty string file types
                    counts[ft] = counts.get(ft, 0) + 1
    except Exception as e:
        print(f"Error getting file type distribution: {e}")
    
    return counts


def get_institution_type_counts():
    """Get file counts by institution type with sub-institutions.
    Uses the institutions table for correct categorization instead of files.institution_type.
    """
    result = {}
    
    try:
        # Get correct institution category from institutions table by joining on institution_name
        # This ensures proper categorization regardless of what's stored in files.institution_type
        type_query = db.session.execute(db.text("""
            SELECT i.category, COUNT(f.file_number) as cnt 
            FROM files f
            INNER JOIN institutions i ON f.institution_name = i.name
            WHERE i.category IS NOT NULL AND i.category != ''
            GROUP BY i.category
            ORDER BY cnt DESC
        """))
        type_counts = type_query.fetchall()
        
        for row in type_counts:
            inst_category = row[0]
            count = row[1]
            
            # Get institutions under this category
            sub_query = db.session.execute(db.text("""
                SELECT f.institution_name, COUNT(f.file_number) as cnt 
                FROM files f
                INNER JOIN institutions i ON f.institution_name = i.name
                WHERE i.category = :category
                AND f.institution_name IS NOT NULL AND f.institution_name != ''
                GROUP BY f.institution_name
                ORDER BY cnt DESC
            """), {'category': inst_category})
            sub_institutions = sub_query.fetchall()
            
            result[inst_category] = {
                'count': count,
                'institutions': {name: cnt for name, cnt in sub_institutions}
            }
        
        # Add files with institution_name that doesn't exist in institutions table
        unmatched_query = db.session.execute(db.text("""
            SELECT f.institution_name, COUNT(f.file_number) as cnt 
            FROM files f
            LEFT JOIN institutions i ON f.institution_name = i.name
            WHERE i.id IS NULL
            AND f.institution_name IS NOT NULL AND f.institution_name != ''
            GROUP BY f.institution_name
            ORDER BY cnt DESC
        """))
        unmatched = unmatched_query.fetchall()
        
        if unmatched:
            result['(Unregistered Institutions)'] = {
                'count': sum(cnt for _, cnt in unmatched),
                'institutions': {name: cnt for name, cnt in unmatched}
            }
    except Exception as e:
        print(f"Error getting institution type counts: {e}")
    
    return result


def get_files_by_year():
    """Get file counts by year with Active/Closed breakdown - matches desktop app logic."""
    import re
    from datetime import datetime
    
    result = {}
    year_pattern = re.compile(r"(19|20)\d{2}")
    current_year = datetime.now().year
    
    try:
        # Get all files with file_year/file_number and is_closed status
        files_query = db.session.execute(db.text("""
            SELECT COALESCE(file_year, file_number) as fy, 
                   COALESCE(is_closed, 0) as status 
            FROM files
        """))
        files_data = files_query.fetchall()
        
        year_counts = {}
        
        for row in files_data:
            fy = row[0]
            is_closed = row[1]
            
            if not fy:
                continue
            
            year = None
            fy_str = str(fy)
            
            # First try: if file_year is a 4-digit year
            if fy_str.isdigit() and len(fy_str) == 4:
                y = int(fy_str)
                if 1900 <= y <= (current_year + 1):
                    year = fy_str
            else:
                # Extract from file_number using regex - find all year patterns
                matches = [m.group(0) for m in year_pattern.finditer(fy_str)]
                # Use the last valid year found (desktop behavior)
                for token in reversed(matches):
                    try:
                        y = int(token)
                        if 1900 <= y <= (current_year + 1):
                            year = str(y)
                            break
                    except Exception:
                        continue
            
            if year:
                if year not in year_counts:
                    year_counts[year] = {'Active': 0, 'Closed': 0, 'Total': 0}
                
                if is_closed == 1:
                    year_counts[year]['Closed'] += 1
                else:
                    year_counts[year]['Active'] += 1
                year_counts[year]['Total'] += 1
        
        # Sort by year descending
        result = dict(sorted(year_counts.items(), key=lambda x: x[0], reverse=True))
        
    except Exception as e:
        print(f"Error getting files by year: {e}")
    
    return result


def get_ua_statistics():
    """Get Unauthorised Absence statistics - matches desktop app logic."""
    stats = {
        'total': 0,
        'total_rejoined': 0,
        'designation_wise': {},
        'total_counts': {
            'Absent': 0,
            'Willingness Given': 0,
            'Rejoined': 0,
            'Retired': 0,
            'MOC Issued': 0,
            'WSD Submitted': 0,
            'SCN Issued': 0,
            'SCN Reply Submitted': 0,
            'Inquiry Conducted': 0,
            'Bond Submitted': 0
        }
    }
    
    try:
        # Total count - Match Disciplinary Action tab logic:
        # Excludes Rejoined, Retired, and records with finalised_date
        total_query = db.session.execute(db.text("""
            SELECT COUNT(*) FROM disciplinary_action_details da
            INNER JOIN unauthorised_absentees ua ON da.id = ua.da_id
            WHERE (ua.present_status IS NULL OR ua.present_status = '' 
                   OR ua.present_status NOT IN ('Rejoined', 'Retired'))
            AND (da.finalised_date IS NULL OR da.finalised_date = '')
        """))
        stats['total'] = total_query.scalar() or 0
        
        # Rejoined count
        rejoined_query = db.session.execute(db.text("""
            SELECT COUNT(*) FROM disciplinary_action_details da
            INNER JOIN unauthorised_absentees ua ON da.id = ua.da_id
            WHERE ua.present_status = 'Rejoined'
        """))
        stats['total_rejoined'] = rejoined_query.scalar() or 0
        
        # Designation-wise counts with all status columns
        designation_query = db.session.execute(db.text("""
            SELECT
                da.designation,
                SUM(CASE WHEN ua.present_status = 'Absent' THEN 1 ELSE 0 END) AS Absent,
                SUM(CASE WHEN ua.willingness = 'Given' THEN 1 ELSE 0 END) AS Willingness_Given,
                SUM(CASE WHEN ua.present_status = 'Rejoined' THEN 1 ELSE 0 END) AS Rejoined,
                SUM(CASE WHEN ua.present_status = 'Retired' THEN 1 ELSE 0 END) AS Retired,
                SUM(CASE WHEN da.moc_issued = 'Issued' THEN 1 ELSE 0 END) AS MOC_Issued,
                SUM(CASE WHEN da.wsd_received_date IS NOT NULL AND da.wsd_received_date != '' THEN 1 ELSE 0 END) AS WSD_Submitted,
                SUM(CASE WHEN da.scn_issued_date IS NOT NULL AND da.scn_issued_date != '' THEN 1 ELSE 0 END) AS SCN_Issued,
                SUM(CASE WHEN da.scn_reply_date IS NOT NULL AND da.scn_reply_date != '' THEN 1 ELSE 0 END) AS SCN_Reply_Submitted,
                SUM(CASE WHEN ua.disc_action_status LIKE '%Inquiry Conducted%' THEN 1 ELSE 0 END) AS Inquiry_Conducted,
                SUM(CASE WHEN ua.bond_submitted = 'YES' THEN 1 ELSE 0 END) AS Bond_Submitted
            FROM
                disciplinary_action_details da
            LEFT JOIN
                unauthorised_absentees ua ON da.id = ua.da_id
            WHERE
                da.unauthorised_others = 'Unauthorised'
            GROUP BY
                da.designation
            ORDER BY
                da.designation
        """))
        
        for row in designation_query.fetchall():
            designation = row[0] or 'Unknown'
            stats['designation_wise'][designation] = {
                'Absent': row[1] or 0,
                'Willingness Given': row[2] or 0,
                'Rejoined': row[3] or 0,
                'Retired': row[4] or 0,
                'MOC Issued': row[5] or 0,
                'WSD Submitted': row[6] or 0,
                'SCN Issued': row[7] or 0,
                'SCN Reply Submitted': row[8] or 0,
                'Inquiry Conducted': row[9] or 0,
                'Bond Submitted': row[10] or 0
            }
        
        # Total counts across all designations
        total_counts_query = db.session.execute(db.text("""
            SELECT
                SUM(CASE WHEN ua.present_status = 'Absent' THEN 1 ELSE 0 END) AS Absent,
                SUM(CASE WHEN ua.willingness = 'Given' THEN 1 ELSE 0 END) AS Willingness_Given,
                SUM(CASE WHEN ua.present_status = 'Rejoined' THEN 1 ELSE 0 END) AS Rejoined,
                SUM(CASE WHEN ua.present_status = 'Retired' THEN 1 ELSE 0 END) AS Retired,
                SUM(CASE WHEN da.moc_issued = 'Issued' THEN 1 ELSE 0 END) AS MOC_Issued,
                SUM(CASE WHEN da.wsd_received_date IS NOT NULL AND da.wsd_received_date != '' THEN 1 ELSE 0 END) AS WSD_Submitted,
                SUM(CASE WHEN da.scn_issued_date IS NOT NULL AND da.scn_issued_date != '' THEN 1 ELSE 0 END) AS SCN_Issued,
                SUM(CASE WHEN da.scn_reply_date IS NOT NULL AND da.scn_reply_date != '' THEN 1 ELSE 0 END) AS SCN_Reply_Submitted,
                SUM(CASE WHEN ua.disc_action_status LIKE '%Inquiry Conducted%' THEN 1 ELSE 0 END) AS Inquiry_Conducted,
                SUM(CASE WHEN ua.bond_submitted = 'YES' THEN 1 ELSE 0 END) AS Bond_Submitted
            FROM
                disciplinary_action_details da
            LEFT JOIN
                unauthorised_absentees ua ON da.id = ua.da_id
            WHERE
                da.unauthorised_others = 'Unauthorised'
        """))
        
        totals = total_counts_query.fetchone()
        if totals:
            stats['total_counts'] = {
                'Absent': totals[0] or 0,
                'Willingness Given': totals[1] or 0,
                'Rejoined': totals[2] or 0,
                'Retired': totals[3] or 0,
                'MOC Issued': totals[4] or 0,
                'WSD Submitted': totals[5] or 0,
                'SCN Issued': totals[6] or 0,
                'SCN Reply Submitted': totals[7] or 0,
                'Inquiry Conducted': totals[8] or 0,
                'Bond Submitted': totals[9] or 0
            }
    except Exception as e:
        print(f"Error getting UA statistics: {e}")
    
    return stats


def get_related_employees():
    """Get all employees from all sources - matches desktop app logic."""
    employees = []
    
    try:
        # 1. From disciplinary_action_details table
        da_query = db.session.execute(db.text("""
            SELECT da.employee_name, da.designation, da.pen, da.file_number, f.subject
            FROM disciplinary_action_details da
            LEFT JOIN files f ON da.file_number = f.file_number
            WHERE da.employee_name IS NOT NULL AND da.employee_name != ''
        """))
        for row in da_query.fetchall():
            employees.append({
                'name': row[0] or '',
                'designation': row[1] or '',
                'pen': row[2] or '',
                'file_number': row[3] or '',
                'subject': row[4] or '',
                'source': 'Disciplinary Action'
            })
        
        # 2. From attacked_doctors table
        try:
            ad_query = db.session.execute(db.text("""
                SELECT ad.name, ad.designation, ad.pen, adc.file_number, f.subject
                FROM attacked_doctors ad
                JOIN attack_on_doctors_cases adc ON ad.case_id = adc.id
                LEFT JOIN files f ON adc.file_number = f.file_number
                WHERE ad.name IS NOT NULL AND ad.name != ''
            """))
            for row in ad_query.fetchall():
                employees.append({
                    'name': row[0] or '',
                    'designation': row[1] or '',
                    'pen': row[2] or '',
                    'file_number': row[3] or '',
                    'subject': row[4] or '',
                    'source': 'Attack on Doctors'
                })
        except Exception:
            pass  # Table may not exist
        
        # 3. From attacked_staffs table
        try:
            as_query = db.session.execute(db.text("""
                SELECT ast.name, ast.designation, ast.pen, asc_t.file_number, f.subject
                FROM attacked_staffs ast
                JOIN attack_on_staffs_cases asc_t ON ast.case_id = asc_t.id
                LEFT JOIN files f ON asc_t.file_number = f.file_number
                WHERE ast.name IS NOT NULL AND ast.name != ''
            """))
            for row in as_query.fetchall():
                employees.append({
                    'name': row[0] or '',
                    'designation': row[1] or '',
                    'pen': row[2] or '',
                    'file_number': row[3] or '',
                    'subject': row[4] or '',
                    'source': 'Attack on Staffs'
                })
        except Exception:
            pass  # Table may not exist
        
        # 4. From wh_employees_involved table (Women Harassment)
        try:
            whe_query = db.session.execute(db.text("""
                SELECT whe.name, whe.designation, whe.pen, whc.file_number, f.subject
                FROM wh_employees_involved whe
                JOIN women_harassment_cases whc ON whe.case_id = whc.id
                LEFT JOIN files f ON whc.file_number = f.file_number
                WHERE whe.name IS NOT NULL AND whe.name != ''
            """))
            for row in whe_query.fetchall():
                employees.append({
                    'name': row[0] or '',
                    'designation': row[1] or '',
                    'pen': row[2] or '',
                    'file_number': row[3] or '',
                    'subject': row[4] or '',
                    'source': 'Women Harassment (Employee)'
                })
        except Exception:
            pass  # Table may not exist
        
        # 5. From wh_culprits_involved table (Women Harassment Culprits)
        try:
            whc_query = db.session.execute(db.text("""
                SELECT whc_inv.name, whc_inv.designation, whc_inv.pen, whc.file_number, f.subject
                FROM wh_culprits_involved whc_inv
                JOIN women_harassment_cases whc ON whc_inv.case_id = whc.id
                LEFT JOIN files f ON whc.file_number = f.file_number
                WHERE whc_inv.name IS NOT NULL AND whc_inv.name != ''
            """))
            for row in whc_query.fetchall():
                employees.append({
                    'name': row[0] or '',
                    'designation': row[1] or '',
                    'pen': row[2] or '',
                    'file_number': row[3] or '',
                    'subject': row[4] or '',
                    'source': 'Women Harassment (Culprit)'
                })
        except Exception:
            pass  # Table may not exist
        
        # Sort by name
        employees.sort(key=lambda x: x['name'].lower() if x['name'] else '')
        
    except Exception as e:
        print(f"Error getting related employees: {e}")
    
    return {
        'total': len(employees),
        'employees': employees
    }


def get_da_years():
    """Get available years from DA records using optimized SQL query."""
    years = set()
    
    try:
        # Use SQL to extract years efficiently instead of loading all records
        # Extract year from DD-MM-YYYY format (last 4 characters) using PostgreSQL RIGHT()
        result = db.session.execute(db.text("""
            SELECT DISTINCT RIGHT(moc_date, 4) as year FROM disciplinary_action_details
            WHERE moc_date IS NOT NULL AND moc_date != '' AND moc_date != 'None' AND LENGTH(moc_date) >= 10
            UNION
            SELECT DISTINCT RIGHT(scn_issued_date, 4) as year FROM disciplinary_action_details
            WHERE scn_issued_date IS NOT NULL AND scn_issued_date != '' AND scn_issued_date != 'None' AND LENGTH(scn_issued_date) >= 10
        """))
        
        for row in result:
            year = row[0]
            if year and year.isdigit() and 1900 <= int(year) <= 2100:
                years.add(year)
                
    except Exception as e:
        print(f"Error getting DA years: {e}")
    
    return sorted(list(years)) if years else ['No data']


def get_da_monthly_stats(selected_year):
    """Get month-wise DA statistics for the selected year using optimized aggregated SQL.
    
    Uses PostgreSQL RIGHT() function instead of substr() for year extraction.
    Matches desktop app logic exactly:
    - MOC DHS: only explicit 'DHS' or 'DMO' values (not including 'None'/empty)
    - SCN DHS: includes NULL, empty, 'None', and 'DHS'
    
    Optimized to use aggregated queries instead of individual queries per month.
    """
    months = ['January', 'February', 'March', 'April', 'May', 'June',
              'July', 'August', 'September', 'October', 'November', 'December']
    
    # Initialize monthly data structure
    monthly_data = {}
    for month_name in months:
        monthly_data[month_name] = {
            'moc_dhs': 0, 'wsd_same_dhs': 0, 'wsd_prev_dhs': 0,
            'moc_govt': 0, 'wsd_same_govt': 0, 'wsd_prev_govt': 0,
            'scn_dhs': 0, 'reply_same_dhs': 0, 'reply_prev_dhs': 0,
            'scn_govt': 0, 'reply_same_govt': 0, 'reply_prev_govt': 0
        }
    
    month_map = {f"{i:02d}": months[i-1] for i in range(1, 13)}
    
    try:
        # Query 1: MOC DHS counts by month
        result = db.session.execute(db.text("""
            SELECT SUBSTRING(moc_date, 4, 2) as month, COUNT(*) as cnt
            FROM disciplinary_action_details
            WHERE RIGHT(moc_date, 4) = :year
            AND (moc_issued_by = 'DHS' OR moc_issued_by = 'DMO')
            AND moc_issued = 'Issued'
            AND LENGTH(moc_date) >= 10
            GROUP BY SUBSTRING(moc_date, 4, 2)
        """), {'year': selected_year})
        for row in result:
            if row[0] in month_map:
                monthly_data[month_map[row[0]]]['moc_dhs'] = row[1]
        
        # Query 2: WSD same month for DHS MOCs
        result = db.session.execute(db.text("""
            SELECT SUBSTRING(moc_date, 4, 2) as month, COUNT(*) as cnt
            FROM disciplinary_action_details
            WHERE RIGHT(moc_date, 4) = :year
            AND RIGHT(wsd_sent_to_dhs_date, 4) = :year
            AND SUBSTRING(moc_date, 4, 2) = SUBSTRING(wsd_sent_to_dhs_date, 4, 2)
            AND (moc_issued_by = 'DHS' OR moc_issued_by = 'DMO')
            AND moc_issued = 'Issued'
            AND wsd_sent_to_dhs_date IS NOT NULL AND wsd_sent_to_dhs_date != '' AND wsd_sent_to_dhs_date != 'None'
            AND LENGTH(moc_date) >= 10 AND LENGTH(wsd_sent_to_dhs_date) >= 10
            GROUP BY SUBSTRING(moc_date, 4, 2)
        """), {'year': selected_year})
        for row in result:
            if row[0] in month_map:
                monthly_data[month_map[row[0]]]['wsd_same_dhs'] = row[1]
        
        # Query 3: WSD prev month for DHS MOCs (WSD forwarded this month, MOC from different month)
        result = db.session.execute(db.text("""
            SELECT SUBSTRING(wsd_sent_to_dhs_date, 4, 2) as month, COUNT(*) as cnt
            FROM disciplinary_action_details
            WHERE RIGHT(moc_date, 4) = :year
            AND RIGHT(wsd_sent_to_dhs_date, 4) = :year
            AND SUBSTRING(moc_date, 4, 2) != SUBSTRING(wsd_sent_to_dhs_date, 4, 2)
            AND (moc_issued_by = 'DHS' OR moc_issued_by = 'DMO')
            AND moc_issued = 'Issued'
            AND wsd_sent_to_dhs_date IS NOT NULL AND wsd_sent_to_dhs_date != '' AND wsd_sent_to_dhs_date != 'None'
            AND LENGTH(moc_date) >= 10 AND LENGTH(wsd_sent_to_dhs_date) >= 10
            GROUP BY SUBSTRING(wsd_sent_to_dhs_date, 4, 2)
        """), {'year': selected_year})
        for row in result:
            if row[0] in month_map:
                monthly_data[month_map[row[0]]]['wsd_prev_dhs'] = row[1]
        
        # Query 4: MOC Govt counts by month
        result = db.session.execute(db.text("""
            SELECT SUBSTRING(moc_date, 4, 2) as month, COUNT(*) as cnt
            FROM disciplinary_action_details
            WHERE RIGHT(moc_date, 4) = :year
            AND moc_issued_by = 'Govt.' AND moc_issued = 'Issued'
            AND LENGTH(moc_date) >= 10
            GROUP BY SUBSTRING(moc_date, 4, 2)
        """), {'year': selected_year})
        for row in result:
            if row[0] in month_map:
                monthly_data[month_map[row[0]]]['moc_govt'] = row[1]
        
        # Query 5: WSD same month for Govt MOCs
        result = db.session.execute(db.text("""
            SELECT SUBSTRING(moc_date, 4, 2) as month, COUNT(*) as cnt
            FROM disciplinary_action_details
            WHERE RIGHT(moc_date, 4) = :year
            AND RIGHT(wsd_sent_to_dhs_date, 4) = :year
            AND SUBSTRING(moc_date, 4, 2) = SUBSTRING(wsd_sent_to_dhs_date, 4, 2)
            AND moc_issued_by = 'Govt.' AND moc_issued = 'Issued'
            AND wsd_sent_to_dhs_date IS NOT NULL AND wsd_sent_to_dhs_date != '' AND wsd_sent_to_dhs_date != 'None'
            AND LENGTH(moc_date) >= 10 AND LENGTH(wsd_sent_to_dhs_date) >= 10
            GROUP BY SUBSTRING(moc_date, 4, 2)
        """), {'year': selected_year})
        for row in result:
            if row[0] in month_map:
                monthly_data[month_map[row[0]]]['wsd_same_govt'] = row[1]
        
        # Query 6: WSD prev month for Govt MOCs
        result = db.session.execute(db.text("""
            SELECT SUBSTRING(wsd_sent_to_dhs_date, 4, 2) as month, COUNT(*) as cnt
            FROM disciplinary_action_details
            WHERE RIGHT(moc_date, 4) = :year
            AND RIGHT(wsd_sent_to_dhs_date, 4) = :year
            AND SUBSTRING(moc_date, 4, 2) != SUBSTRING(wsd_sent_to_dhs_date, 4, 2)
            AND moc_issued_by = 'Govt.' AND moc_issued = 'Issued'
            AND wsd_sent_to_dhs_date IS NOT NULL AND wsd_sent_to_dhs_date != '' AND wsd_sent_to_dhs_date != 'None'
            AND LENGTH(moc_date) >= 10 AND LENGTH(wsd_sent_to_dhs_date) >= 10
            GROUP BY SUBSTRING(wsd_sent_to_dhs_date, 4, 2)
        """), {'year': selected_year})
        for row in result:
            if row[0] in month_map:
                monthly_data[month_map[row[0]]]['wsd_prev_govt'] = row[1]
        
        # Query 7: SCN DHS counts by month
        result = db.session.execute(db.text("""
            SELECT SUBSTRING(scn_issued_date, 4, 2) as month, COUNT(*) as cnt
            FROM disciplinary_action_details
            WHERE RIGHT(scn_issued_date, 4) = :year
            AND (scn_issued_by IS NULL OR scn_issued_by = '' OR scn_issued_by = 'None' OR scn_issued_by = 'DHS')
            AND scn_issued_date IS NOT NULL AND scn_issued_date != '' AND scn_issued_date != 'None'
            AND LENGTH(scn_issued_date) >= 10
            GROUP BY SUBSTRING(scn_issued_date, 4, 2)
        """), {'year': selected_year})
        for row in result:
            if row[0] in month_map:
                monthly_data[month_map[row[0]]]['scn_dhs'] = row[1]
        
        # Query 8: Reply same month for DHS SCNs
        result = db.session.execute(db.text("""
            SELECT SUBSTRING(scn_issued_date, 4, 2) as month, COUNT(*) as cnt
            FROM disciplinary_action_details
            WHERE RIGHT(scn_issued_date, 4) = :year
            AND RIGHT(scn_reply_sent_to_dhs_date, 4) = :year
            AND SUBSTRING(scn_issued_date, 4, 2) = SUBSTRING(scn_reply_sent_to_dhs_date, 4, 2)
            AND (scn_issued_by IS NULL OR scn_issued_by = '' OR scn_issued_by = 'None' OR scn_issued_by = 'DHS')
            AND scn_reply_sent_to_dhs_date IS NOT NULL AND scn_reply_sent_to_dhs_date != '' AND scn_reply_sent_to_dhs_date != 'None'
            AND LENGTH(scn_issued_date) >= 10 AND LENGTH(scn_reply_sent_to_dhs_date) >= 10
            GROUP BY SUBSTRING(scn_issued_date, 4, 2)
        """), {'year': selected_year})
        for row in result:
            if row[0] in month_map:
                monthly_data[month_map[row[0]]]['reply_same_dhs'] = row[1]
        
        # Query 9: Reply prev month for DHS SCNs
        result = db.session.execute(db.text("""
            SELECT SUBSTRING(scn_reply_sent_to_dhs_date, 4, 2) as month, COUNT(*) as cnt
            FROM disciplinary_action_details
            WHERE RIGHT(scn_issued_date, 4) = :year
            AND RIGHT(scn_reply_sent_to_dhs_date, 4) = :year
            AND SUBSTRING(scn_issued_date, 4, 2) != SUBSTRING(scn_reply_sent_to_dhs_date, 4, 2)
            AND (scn_issued_by IS NULL OR scn_issued_by = '' OR scn_issued_by = 'None' OR scn_issued_by = 'DHS')
            AND scn_reply_sent_to_dhs_date IS NOT NULL AND scn_reply_sent_to_dhs_date != '' AND scn_reply_sent_to_dhs_date != 'None'
            AND LENGTH(scn_issued_date) >= 10 AND LENGTH(scn_reply_sent_to_dhs_date) >= 10
            GROUP BY SUBSTRING(scn_reply_sent_to_dhs_date, 4, 2)
        """), {'year': selected_year})
        for row in result:
            if row[0] in month_map:
                monthly_data[month_map[row[0]]]['reply_prev_dhs'] = row[1]
        
        # Query 10: SCN Govt counts by month
        result = db.session.execute(db.text("""
            SELECT SUBSTRING(scn_issued_date, 4, 2) as month, COUNT(*) as cnt
            FROM disciplinary_action_details
            WHERE RIGHT(scn_issued_date, 4) = :year
            AND scn_issued_by = 'Govt.'
            AND scn_issued_date IS NOT NULL AND scn_issued_date != '' AND scn_issued_date != 'None'
            AND LENGTH(scn_issued_date) >= 10
            GROUP BY SUBSTRING(scn_issued_date, 4, 2)
        """), {'year': selected_year})
        for row in result:
            if row[0] in month_map:
                monthly_data[month_map[row[0]]]['scn_govt'] = row[1]
        
        # Query 11: Reply same month for Govt SCNs
        result = db.session.execute(db.text("""
            SELECT SUBSTRING(scn_issued_date, 4, 2) as month, COUNT(*) as cnt
            FROM disciplinary_action_details
            WHERE RIGHT(scn_issued_date, 4) = :year
            AND RIGHT(scn_reply_sent_to_dhs_date, 4) = :year
            AND SUBSTRING(scn_issued_date, 4, 2) = SUBSTRING(scn_reply_sent_to_dhs_date, 4, 2)
            AND scn_issued_by = 'Govt.'
            AND scn_reply_sent_to_dhs_date IS NOT NULL AND scn_reply_sent_to_dhs_date != '' AND scn_reply_sent_to_dhs_date != 'None'
            AND LENGTH(scn_issued_date) >= 10 AND LENGTH(scn_reply_sent_to_dhs_date) >= 10
            GROUP BY SUBSTRING(scn_issued_date, 4, 2)
        """), {'year': selected_year})
        for row in result:
            if row[0] in month_map:
                monthly_data[month_map[row[0]]]['reply_same_govt'] = row[1]
        
        # Query 12: Reply prev month for Govt SCNs
        result = db.session.execute(db.text("""
            SELECT SUBSTRING(scn_reply_sent_to_dhs_date, 4, 2) as month, COUNT(*) as cnt
            FROM disciplinary_action_details
            WHERE RIGHT(scn_issued_date, 4) = :year
            AND RIGHT(scn_reply_sent_to_dhs_date, 4) = :year
            AND SUBSTRING(scn_issued_date, 4, 2) != SUBSTRING(scn_reply_sent_to_dhs_date, 4, 2)
            AND scn_issued_by = 'Govt.'
            AND scn_reply_sent_to_dhs_date IS NOT NULL AND scn_reply_sent_to_dhs_date != '' AND scn_reply_sent_to_dhs_date != 'None'
            AND LENGTH(scn_issued_date) >= 10 AND LENGTH(scn_reply_sent_to_dhs_date) >= 10
            GROUP BY SUBSTRING(scn_reply_sent_to_dhs_date, 4, 2)
        """), {'year': selected_year})
        for row in result:
            if row[0] in month_map:
                monthly_data[month_map[row[0]]]['reply_prev_govt'] = row[1]
    
    except Exception as e:
        print(f"Error getting DA monthly stats: {e}")
        import traceback
        traceback.print_exc()
    
    # Add "Previous Data" - all records from years before selected year
    previous_data = {
        'moc_dhs': 0, 'wsd_same_dhs': 0, 'wsd_prev_dhs': 0,
        'moc_govt': 0, 'wsd_same_govt': 0, 'wsd_prev_govt': 0,
        'scn_dhs': 0, 'reply_same_dhs': 0, 'reply_prev_dhs': 0,
        'scn_govt': 0, 'reply_same_govt': 0, 'reply_prev_govt': 0
    }
    
    try:
        # Previous MOC DHS
        result = db.session.execute(db.text("""
            SELECT COUNT(*) FROM disciplinary_action_details
            WHERE RIGHT(moc_date, 4) < :year
            AND (moc_issued_by = 'DHS' OR moc_issued_by = 'DMO')
            AND moc_issued = 'Issued'
            AND LENGTH(moc_date) >= 10
        """), {'year': selected_year})
        previous_data['moc_dhs'] = result.scalar() or 0
        
        # Previous MOC Govt
        result = db.session.execute(db.text("""
            SELECT COUNT(*) FROM disciplinary_action_details
            WHERE RIGHT(moc_date, 4) < :year
            AND moc_issued_by = 'Govt.' AND moc_issued = 'Issued'
            AND LENGTH(moc_date) >= 10
        """), {'year': selected_year})
        previous_data['moc_govt'] = result.scalar() or 0
        
        # Previous SCN DHS
        result = db.session.execute(db.text("""
            SELECT COUNT(*) FROM disciplinary_action_details
            WHERE RIGHT(scn_issued_date, 4) < :year
            AND (scn_issued_by IS NULL OR scn_issued_by = '' OR scn_issued_by = 'None' OR scn_issued_by = 'DHS')
            AND scn_issued_date IS NOT NULL AND scn_issued_date != '' AND scn_issued_date != 'None'
            AND LENGTH(scn_issued_date) >= 10
        """), {'year': selected_year})
        previous_data['scn_dhs'] = result.scalar() or 0
        
        # Previous SCN Govt
        result = db.session.execute(db.text("""
            SELECT COUNT(*) FROM disciplinary_action_details
            WHERE RIGHT(scn_issued_date, 4) < :year
            AND scn_issued_by = 'Govt.'
            AND scn_issued_date IS NOT NULL AND scn_issued_date != '' AND scn_issued_date != 'None'
            AND LENGTH(scn_issued_date) >= 10
        """), {'year': selected_year})
        previous_data['scn_govt'] = result.scalar() or 0
        
    except Exception as e:
        print(f"Error getting previous data: {e}")
    
    # Add previous data as a special entry
    monthly_data['Previous Data'] = previous_data
    
    return monthly_data


def parse_date_year_month(date_str):
    """Parse DD-MM-YYYY date string and return (year, month)."""
    if not date_str or len(date_str) < 10:
        return None, None
    try:
        # DD-MM-YYYY format
        parts = date_str.split('-')
        if len(parts) == 3:
            return parts[2], parts[1]  # year, month
    except:
        pass
    return None, None


@reports_bp.route('/api/da-monthly-stats/<year>')
@login_required
def api_da_monthly_stats(year):
    """API endpoint for DA monthly statistics."""
    stats = get_da_monthly_stats(year)
    return jsonify(stats)


@reports_bp.route('/export-da-overview/<year>')
@login_required
def export_da_overview(year):
    """Export DA Overview to CSV."""
    stats = get_da_monthly_stats(year)
    
    output = io.StringIO()
    # Add UTF-8 BOM for Excel to recognize Unicode characters (Malayalam etc.)
    output.write('\ufeff')
    writer = csv.writer(output)
    
    # Header
    writer.writerow([
        'Month',
        'MOC from DHS', 'WSD Same Month (DHS)', 'WSD Prev Month (DHS)',
        'MOC from Govt', 'WSD Same Month (Govt)', 'WSD Prev Month (Govt)',
        'SCN from DHS', 'Reply Same Month (DHS)', 'Reply Prev Month (DHS)',
        'SCN from Govt', 'Reply Same Month (Govt)', 'Reply Prev Month (Govt)'
    ])
    
    months = ['January', 'February', 'March', 'April', 'May', 'June',
              'July', 'August', 'September', 'October', 'November', 'December']
    
    for month in months:
        if month in stats:
            m = stats[month]
            writer.writerow([
                month,
                m['moc_dhs'], m['wsd_same_dhs'], m['wsd_prev_dhs'],
                m['moc_govt'], m['wsd_same_govt'], m['wsd_prev_govt'],
                m['scn_dhs'], m['reply_same_dhs'], m['reply_prev_dhs'],
                m['scn_govt'], m['reply_same_govt'], m['reply_prev_govt']
            ])
    
    # Add Previous Data row
    if 'Previous Data' in stats:
        prev = stats['Previous Data']
        writer.writerow([
            'Previous Data',
            prev['moc_dhs'], prev['wsd_same_dhs'], prev['wsd_prev_dhs'],
            prev['moc_govt'], prev['wsd_same_govt'], prev['wsd_prev_govt'],
            prev['scn_dhs'], prev['reply_same_dhs'], prev['reply_prev_dhs'],
            prev['scn_govt'], prev['reply_same_govt'], prev['reply_prev_govt']
        ])
    
    output.seek(0)
    
    return Response(
        output.getvalue().encode('utf-8-sig'),
        mimetype='text/csv; charset=utf-8-sig',
        headers={'Content-Disposition': f'attachment; filename=DA_Overview_{year}.csv'}
    )


@reports_bp.route('/export-related-employees')
@login_required
def export_related_employees():
    """Export Related Employees to CSV."""
    employees_data = get_related_employees()
    employees = employees_data.get('employees', [])
    
    output = io.StringIO()
    # Add UTF-8 BOM for Excel to recognize Unicode characters (Malayalam etc.)
    output.write('\ufeff')
    writer = csv.writer(output)
    
    # Header matching desktop app columns
    writer.writerow(['Sl.No.', 'Name', 'Designation', 'PEN', 'File Number', 'Subject', 'Source'])
    
    # Write data
    for i, emp in enumerate(employees, 1):
        writer.writerow([
            i,
            emp.get('name', ''),
            emp.get('designation', ''),
            emp.get('pen', ''),
            emp.get('file_number', ''),
            emp.get('subject', ''),
            emp.get('source', '')
        ])
    
    output.seek(0)
    
    return Response(
        output.getvalue().encode('utf-8-sig'),
        mimetype='text/csv; charset=utf-8-sig',
        headers={'Content-Disposition': 'attachment; filename=Related_Employees.csv'}
    )


@reports_bp.route('/file-summary')
@login_required
def file_summary():
    """File summary report."""
    # Get counts by status
    status_counts = db.session.query(
        File.status, func.count(File.file_number)
    ).group_by(File.status).all()
    
    # Get counts by category
    category_counts = db.session.query(
        File.category, func.count(File.file_number)
    ).group_by(File.category).all()
    
    # Get counts by year
    year_counts = db.session.query(
        func.substr(File.file_number, 1, 4), func.count(File.file_number)
    ).group_by(func.substr(File.file_number, 1, 4)).order_by(
        func.substr(File.file_number, 1, 4).desc()
    ).limit(10).all()
    
    return render_template('reports/file_summary.html',
                          status_counts=status_counts,
                          category_counts=category_counts,
                          year_counts=year_counts)


@reports_bp.route('/disciplinary-summary')
@login_required
def disciplinary_summary():
    """Disciplinary action summary report."""
    # Total disciplinary actions
    total_da = DisciplinaryAction.query.count()
    
    # Get counts by institution
    institution_counts = db.session.query(
        DisciplinaryAction.institution, func.count(DisciplinaryAction.id)
    ).group_by(DisciplinaryAction.institution).order_by(
        func.count(DisciplinaryAction.id).desc()
    ).limit(20).all()
    
    # Get major/minor counts
    type_counts = db.session.query(
        DisciplinaryAction.major_minor, func.count(DisciplinaryAction.id)
    ).group_by(DisciplinaryAction.major_minor).all()
    
    # Unauthorised absentees count
    ua_count = UnauthorisedAbsentee.query.count()
    
    # Pending cases (not finalised)
    pending_count = DisciplinaryAction.query.filter(
        or_(
            DisciplinaryAction.finalised_date == None,
            DisciplinaryAction.finalised_date == ''
        )
    ).count()
    
    return render_template('reports/disciplinary_summary.html',
                          total_da=total_da,
                          institution_counts=institution_counts,
                          type_counts=type_counts,
                          ua_count=ua_count,
                          pending_count=pending_count)


@reports_bp.route('/rti-summary')
@login_required
def rti_summary():
    """RTI application summary report."""
    # Total RTI applications
    total_rti = RTIApplication.query.count()
    
    # Get counts by status
    status_counts = db.session.query(
        RTIApplication.status, func.count(RTIApplication.id)
    ).group_by(RTIApplication.status).all()
    
    # Get counts by appeal status
    appeal_counts = db.session.query(
        RTIApplication.appeal_status, func.count(RTIApplication.id)
    ).filter(RTIApplication.appeal_status != None, RTIApplication.appeal_status != '').group_by(
        RTIApplication.appeal_status
    ).all()
    
    # Pending applications
    pending_count = RTIApplication.query.filter(RTIApplication.status != 'Disposed').count()
    
    # Year-wise counts
    year_counts = db.session.query(
        func.substr(RTIApplication.application_date, 7, 4), func.count(RTIApplication.id)
    ).group_by(func.substr(RTIApplication.application_date, 7, 4)).order_by(
        func.substr(RTIApplication.application_date, 7, 4).desc()
    ).limit(5).all()
    
    return render_template('reports/rti_summary.html',
                          total_rti=total_rti,
                          status_counts=status_counts,
                          appeal_counts=appeal_counts,
                          pending_count=pending_count,
                          year_counts=year_counts)


@reports_bp.route('/pending-files')
@login_required
def pending_files():
    """Pending files report."""
    page = request.args.get('page', 1, type=int)
    per_page = 50
    
    category = request.args.get('category', '')
    
    query = File.query.filter(
        or_(
            File.status == 'Pending',
            File.status == 'Open',
            File.status == None
        )
    )
    
    if category:
        query = query.filter(File.category == category)
    
    query = query.order_by(File.file_number.asc())
    
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    files = pagination.items
    
    # Get categories for filter
    categories = db.session.query(File.category).distinct().filter(
        File.category != None, File.category != ''
    ).all()
    categories = [c[0] for c in categories]
    
    return render_template('reports/pending_files.html',
                          files=files,
                          pagination=pagination,
                          categories=categories,
                          selected_category=category)


@reports_bp.route('/closed-files')
@login_required
def closed_files():
    """Closed files report."""
    page = request.args.get('page', 1, type=int)
    per_page = 50
    
    from_date = request.args.get('from_date', '')
    to_date = request.args.get('to_date', '')
    
    query = File.query.filter(File.status == 'Closed')
    
    # Date filtering if provided
    if from_date and to_date:
        query = query.filter(
            and_(
                File.file_closed_date >= from_date,
                File.file_closed_date <= to_date
            )
        )
    
    query = query.order_by(File.file_closed_date.desc())
    
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    files = pagination.items
    
    return render_template('reports/closed_files.html',
                          files=files,
                          pagination=pagination,
                          from_date=from_date,
                          to_date=to_date)


@reports_bp.route('/ua-report')
@login_required
def ua_report():
    """Unauthorised absentees report."""
    page = request.args.get('page', 1, type=int)
    per_page = 50
    
    status_filter = request.args.get('status', '')
    
    query = db.session.query(DisciplinaryAction, UnauthorisedAbsentee).join(
        UnauthorisedAbsentee, DisciplinaryAction.id == UnauthorisedAbsentee.da_id
    )
    
    if status_filter:
        query = query.filter(UnauthorisedAbsentee.present_status == status_filter)
    
    query = query.order_by(DisciplinaryAction.id.desc())
    
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    results = pagination.items
    
    # Get unique statuses for filter
    statuses = db.session.query(UnauthorisedAbsentee.present_status).distinct().filter(
        UnauthorisedAbsentee.present_status != None, UnauthorisedAbsentee.present_status != ''
    ).all()
    statuses = [s[0] for s in statuses]
    
    return render_template('reports/ua_report.html',
                          results=results,
                          pagination=pagination,
                          statuses=statuses,
                          status_filter=status_filter)


@reports_bp.route('/court-cases')
@login_required
def court_cases():
    """Court cases report."""
    page = request.args.get('page', 1, type=int)
    per_page = 50
    
    status_filter = request.args.get('status', '')
    court_type = request.args.get('court_type', '')
    year = request.args.get('year', '')
    
    query = CourtCase.query
    
    if status_filter:
        query = query.filter(CourtCase.present_status == status_filter)
    if court_type:
        query = query.filter(CourtCase.name_of_forum == court_type)
    if year:
        query = query.filter(CourtCase.year == year)
    
    query = query.order_by(CourtCase.id.desc())
    
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    cases = pagination.items
    
    # Get unique statuses
    statuses = db.session.query(CourtCase.present_status).distinct().filter(
        CourtCase.present_status != None, CourtCase.present_status != ''
    ).all()
    statuses = [s[0] for s in statuses]
    
    # Get unique years
    years = db.session.query(CourtCase.year).distinct().filter(
        CourtCase.year != None, CourtCase.year != ''
    ).all()
    years = sorted([y[0] for y in years], reverse=True)
    
    # Summary stats
    summary = {
        'total': CourtCase.query.count(),
        'pending': CourtCase.query.filter(CourtCase.present_status == 'Pending').count(),
        'disposed': CourtCase.query.filter(CourtCase.present_status == 'Disposed').count(),
        'stayed': CourtCase.query.filter(CourtCase.present_status == 'Stayed').count()
    }
    
    # Court-wise summary
    court_summary = []
    
    return render_template('reports/court_cases.html',
                          cases=cases,
                          pagination=pagination,
                          statuses=statuses,
                          status_filter=status_filter,
                          court_type=court_type,
                          year=year,
                          years=years,
                          summary=summary,
                          court_summary=court_summary,
                          upcoming_hearings=[])


@reports_bp.route('/court-case/<int:id>')
@login_required
def view_court_case(id):
    """View court case details."""
    case = CourtCase.query.get_or_404(id)
    return redirect(url_for('files.view_file', file_number=case.file_number))


@reports_bp.route('/inquiries')
@login_required
def inquiries():
    """Inquiries report."""
    page = request.args.get('page', 1, type=int)
    per_page = 50
    
    inquiry_type_filter = request.args.get('inquiry_type', '')
    
    query = InquiryDetails.query
    
    # Filter by inquiry type
    if inquiry_type_filter == 'prelim':
        query = query.filter(InquiryDetails.prelim_conducted == 1)
    elif inquiry_type_filter == 'rule15':
        query = query.filter(InquiryDetails.rule15_conducted == 1)
    
    query = query.order_by(InquiryDetails.id.desc())
    
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    inquiries_list = pagination.items
    
    return render_template('reports/inquiries.html',
                          inquiries=inquiries_list,
                          pagination=pagination,
                          inquiry_type_filter=inquiry_type_filter)


@reports_bp.route('/women-harassment')
@login_required
def women_harassment():
    """Women harassment cases report."""
    page = request.args.get('page', 1, type=int)
    per_page = 50
    
    status_filter = request.args.get('status', '')
    
    query = WomenHarassmentCase.query
    
    if status_filter:
        query = query.filter(WomenHarassmentCase.case_status == status_filter)
    
    query = query.order_by(WomenHarassmentCase.id.desc())
    
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    cases = pagination.items
    
    # Get unique statuses
    statuses = db.session.query(WomenHarassmentCase.case_status).distinct().filter(
        WomenHarassmentCase.case_status != None, WomenHarassmentCase.case_status != ''
    ).all()
    statuses = [s[0] for s in statuses]
    
    return render_template('reports/women_harassment.html',
                          cases=cases,
                          pagination=pagination,
                          statuses=statuses,
                          status_filter=status_filter)


@reports_bp.route('/social-security')
@login_required
def social_security():
    """Social security pension report."""
    page = request.args.get('page', 1, type=int)
    per_page = 50
    
    status_filter = request.args.get('status', '')
    
    query = SocialSecurityPension.query
    
    if status_filter:
        query = query.filter(SocialSecurityPension.status == status_filter)
    
    query = query.order_by(SocialSecurityPension.id.desc())
    
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    records = pagination.items
    
    # Get unique statuses
    statuses = db.session.query(SocialSecurityPension.status).distinct().filter(
        SocialSecurityPension.status != None, SocialSecurityPension.status != ''
    ).all()
    statuses = [s[0] for s in statuses]
    
    return render_template('reports/social_security.html',
                          records=records,
                          pagination=pagination,
                          statuses=statuses,
                          status_filter=status_filter)


@reports_bp.route('/export/<report_type>')
@login_required
def export_report(report_type):
    """Export report to CSV."""
    output = io.StringIO()
    # Add UTF-8 BOM for Excel to recognize Unicode characters (Malayalam etc.)
    output.write('\ufeff')
    writer = csv.writer(output)
    
    if report_type == 'pending-files':
        files = File.query.filter(
            or_(File.status == 'Pending', File.status == 'Open', File.status == None)
        ).order_by(File.file_number.asc()).all()
        
        writer.writerow(['File Number', 'Category', 'Subject', 'Date of Receipt', 'From Whom Received'])
        for f in files:
            writer.writerow([f.file_number, f.category, f.subject, f.date_of_receipt, f.from_whom_received])
    
    elif report_type == 'closed-files':
        files = File.query.filter(File.status == 'Closed').order_by(File.file_closed_date.desc()).all()
        
        writer.writerow(['File Number', 'Category', 'Subject', 'Date Closed', 'Closing Remarks'])
        for f in files:
            writer.writerow([f.file_number, f.category, f.subject, f.file_closed_date, f.closing_remarks])
    
    elif report_type == 'ua':
        results = db.session.query(DisciplinaryAction, UnauthorisedAbsentee).join(
            UnauthorisedAbsentee, DisciplinaryAction.id == UnauthorisedAbsentee.da_id
        ).all()
        
        writer.writerow(['File Number', 'PEN', 'Name', 'Institution', 'UA From Date', 'Present Status'])
        for da, ua in results:
            writer.writerow([da.file_number, da.pen, da.employee_name, da.institution, ua.date_from_ua, ua.present_status])
    
    elif report_type == 'rti':
        applications = RTIApplication.query.order_by(RTIApplication.id.desc()).all()
        
        writer.writerow(['File Number', 'Applicant', 'Subject', 'Application Date', 'Status', 'Appeal Status'])
        for app in applications:
            writer.writerow([app.file_number, app.applicant_name, app.subject, app.application_date, app.status, app.appeal_status])
    
    else:
        writer.writerow(['Error: Unknown report type'])
    
    output.seek(0)
    
    return Response(
        output.getvalue().encode('utf-8-sig'),
        mimetype='text/csv; charset=utf-8-sig',
        headers={'Content-Disposition': f'attachment; filename={report_type}_report.csv'}
    )


@reports_bp.route('/custom')
@login_required
def custom():
    """Custom report builder."""
    return render_template('reports/custom.html')


@reports_bp.route('/custom/generate', methods=['POST'], endpoint='custom_result')
@login_required
def generate_custom_report():
    """Generate custom report based on user selections."""
    report_type = request.form.get('report_type', 'files')
    fields = request.form.getlist('fields')
    filters = {}
    
    # Get filter values
    for key in request.form.keys():
        if key.startswith('filter_'):
            filter_name = key[7:]
            filter_value = request.form.get(key)
            if filter_value:
                filters[filter_name] = filter_value
    
    # Build query based on report type
    if report_type == 'files':
        query = File.query
        for filter_name, filter_value in filters.items():
            if hasattr(File, filter_name):
                query = query.filter(getattr(File, filter_name).ilike(f'%{filter_value}%'))
        records = query.all()
    elif report_type == 'disciplinary':
        query = DisciplinaryAction.query
        for filter_name, filter_value in filters.items():
            if hasattr(DisciplinaryAction, filter_name):
                query = query.filter(getattr(DisciplinaryAction, filter_name).ilike(f'%{filter_value}%'))
        records = query.all()
    elif report_type == 'rti':
        query = RTIApplication.query
        for filter_name, filter_value in filters.items():
            if hasattr(RTIApplication, filter_name):
                query = query.filter(getattr(RTIApplication, filter_name).ilike(f'%{filter_value}%'))
        records = query.all()
    else:
        records = []
    
    return render_template('reports/custom_result.html',
                          records=records,
                          fields=fields,
                          report_type=report_type)
