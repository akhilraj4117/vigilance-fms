"""
Vigilance File Management System - Flask Web Application
Main application entry point.
"""
import os
from flask import Flask
from config import config
from extensions import db, login_manager, csrf
from sqlalchemy import event
from sqlalchemy.engine import Engine


# Register event listener globally BEFORE any engine is created
# This disables prepared statements for psycopg3 connections (required for connection pooling)
@event.listens_for(Engine, "connect")
def set_prepare_threshold(dbapi_connection, connection_record):
    """Disable prepared statements for psycopg3 connections."""
    try:
        dbapi_connection.prepare_threshold = 0
    except AttributeError:
        pass  # Not a psycopg3 connection


def create_app(config_name=None):
    """Application factory function."""
    
    if config_name is None:
        config_name = os.environ.get('FLASK_CONFIG', 'default')
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    
    # Configure login manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    # Register blueprints
    from routes.auth import auth_bp
    from routes.main import main_bp
    from routes.files import files_bp
    from routes.disciplinary import disciplinary_bp
    from routes.rti import rti_bp
    from routes.reports import reports_bp
    from routes.institutions import institutions_bp
    from routes.employees import employees_bp
    from routes.api import api_bp
    from routes.file_movements import file_movements_bp
    from routes.committees import committees_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(main_bp)
    app.register_blueprint(files_bp, url_prefix='/files')
    app.register_blueprint(disciplinary_bp, url_prefix='/disciplinary')
    app.register_blueprint(rti_bp, url_prefix='/rti')
    app.register_blueprint(reports_bp, url_prefix='/reports')
    app.register_blueprint(institutions_bp, url_prefix='/institutions')
    app.register_blueprint(employees_bp, url_prefix='/employees')
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(file_movements_bp, url_prefix='/file-movements')
    app.register_blueprint(committees_bp)
    
    # Create database tables only for new tables (users)
    with app.app_context():
        # Only create the users table if it doesn't exist
        # Don't create other tables as they already exist in the desktop database
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        existing_tables = inspector.get_table_names()
        
        # Only create users table if it doesn't exist
        if 'users' not in existing_tables:
            from models import User
            User.__table__.create(db.engine)
        
        # Create categories and file_types tables if they don't exist
        if 'categories' not in existing_tables:
            from models import Category
            Category.__table__.create(db.engine)
            print("Created categories table")
        
        if 'file_types' not in existing_tables:
            from models import FileType
            FileType.__table__.create(db.engine)
            print("Created file_types table")
        
        # Create committees and committee_members tables if they don't exist
        if 'committees' not in existing_tables:
            from models import Committee
            Committee.__table__.create(db.engine)
            print("Created committees table")
        
        if 'committee_members' not in existing_tables:
            from models import CommitteeMember
            CommitteeMember.__table__.create(db.engine)
            print("Created committee_members table")
        
        # Initialize default categories and file types
        from models import Category, FileType
        
        # Default file types
        default_file_types = [
            "Women Harassment", "Police Case", "Medical Negligence",
            "Attack on Doctors", "Attack on Staffs", "Unauthorised Absence",
            "RTI", "Duty Lapse", "Private Practice", "Denial of Treatment",
            "Social Security Pension", "Others"
        ]
        
        # Default categories
        default_categories = [
            "CMO Portal", "RVU", "KeSCPCR", "KHRC", "NKS",
            "SC/ST", "KWC", "Court Case", "Rajya/Lok/Niyamasabha",
            "Vig & Anti Corruption", "Complaint", "Others"
        ]
        
        # Add file types if they don't exist
        for ft_name in default_file_types:
            if not FileType.query.filter_by(name=ft_name).first():
                ft = FileType(name=ft_name)
                db.session.add(ft)
        
        # Add categories if they don't exist
        for cat_name in default_categories:
            if not Category.query.filter_by(name=cat_name).first():
                cat = Category(name=cat_name)
                db.session.add(cat)
        
        try:
            db.session.commit()
        except:
            db.session.rollback()
        
        # Initialize default users
        from routes.auth import init_default_users
        init_default_users()
    
    # Register error handlers
    register_error_handlers(app)
    
    # Register custom filters
    register_custom_filters(app)
    
    # Register context processors
    @app.context_processor
    def inject_globals():
        return {
            'app_name': app.config['APP_NAME'],
            'organization': app.config['ORGANIZATION']
        }
    
    return app


def register_custom_filters(app):
    """Register custom Jinja2 filters."""
    from datetime import datetime
    
    @app.template_filter('format_date')
    def format_date_filter(date_str):
        """Format date string to DD-MM-YYYY format.
        Handles multiple input formats including American MM/DD/YYYY format.
        """
        if not date_str or date_str == '-' or not str(date_str).strip():
            return '-'
        
        date_str = str(date_str).strip()
        
        # Try different date formats - ORDER MATTERS!
        formats_to_try = [
            # Unambiguous formats (year first or text month)
            '%Y-%m-%d',      # YYYY-MM-DD (HTML date input format) - MOST COMMON
            '%Y/%m/%d',      # YYYY/MM/DD
            '%Y.%m.%d',      # YYYY.MM.DD
            '%d %b %Y',      # 15 Jan 2024
            '%d-%b-%Y',      # 15-Jan-2024
            '%b %d %Y',      # Jan 15 2024
            '%b %d, %Y',     # Jan 15, 2024
            '%d %B %Y',      # 15 January 2024
            '%B %d %Y',      # January 15 2024
            '%B %d, %Y',     # January 15, 2024
            
            # DD/MM/YYYY formats (European - day first) - TRY FIRST for ambiguous
            '%d/%m/%Y',      # DD/MM/YYYY (European)
            '%d-%m-%Y',      # DD-MM-YYYY (European)
            '%d.%m.%Y',      # DD.MM.YYYY (European)
            '%d %m %Y',      # DD MM YYYY (European with spaces)
            
            # MM/DD/YYYY formats (American - month first)
            '%m/%d/%Y',      # MM/DD/YYYY (American)
            '%m-%d-%Y',      # MM-DD-YYYY (American)
            '%m %d %Y',      # MM DD YYYY (American with spaces)
        ]
        
        for fmt in formats_to_try:
            try:
                date_obj = datetime.strptime(date_str, fmt)
                return date_obj.strftime('%d-%m-%Y')
            except ValueError:
                continue
        
        # Special handling for ambiguous dates
        for separator in ['/', '-', ' ', '.']:
            parts = date_str.split(separator)
            if len(parts) == 3:
                try:
                    first = int(parts[0])
                    second = int(parts[1])
                    third = int(parts[2])
                    
                    if third > 31:  # Year is last
                        year = third
                        if first > 12:  # First must be day (European)
                            day, month = first, second
                        elif second > 12:  # Second must be day (American)
                            month, day = first, second
                        else:  # Ambiguous - assume European DD/MM/YYYY
                            day, month = first, second
                    elif first > 31:  # Year is first
                        year = first
                        month, day = second, third
                    else:
                        continue
                    
                    if 1 <= month <= 12 and 1 <= day <= 31 and 1900 <= year <= 2100:
                        return f'{day:02d}-{month:02d}-{year}'
                except (ValueError, IndexError):
                    continue
        
        return date_str
    
    @app.template_filter('format_date_html')
    def format_date_html_filter(date_str):
        """Convert date string to YYYY-MM-DD format for HTML date input.
        Handles various date formats from database including American format.
        """
        if not date_str or date_str == '-' or not str(date_str).strip():
            return ''
        
        date_str = str(date_str).strip()
        
        # Try different date formats and convert to YYYY-MM-DD
        formats_to_try = [
            '%d-%m-%Y',      # DD-MM-YYYY (stored format)
            '%d/%m/%Y',      # DD/MM/YYYY (European)
            '%Y-%m-%d',      # Already in HTML format
            '%d.%m.%Y',      # DD.MM.YYYY
            '%m/%d/%Y',      # MM/DD/YYYY (American)
            '%m-%d-%Y',      # MM-DD-YYYY (American)
            '%m %d %Y',      # MM DD YYYY (American with spaces)
            '%d %b %Y',      # 15 Jan 2024
            '%b %d %Y',      # Jan 15 2024
        ]
        
        for fmt in formats_to_try:
            try:
                date_obj = datetime.strptime(date_str, fmt)
                return date_obj.strftime('%Y-%m-%d')
            except ValueError:
                continue
        
        # Special handling for ambiguous dates
        for separator in ['/', '-', ' ', '.']:
            parts = date_str.split(separator)
            if len(parts) == 3:
                try:
                    first = int(parts[0])
                    second = int(parts[1])
                    third = int(parts[2])
                    
                    if third > 31:  # Year is last
                        year = third
                        if first > 12:  # First must be day
                            day, month = first, second
                        elif second > 12:  # Second must be day
                            month, day = first, second
                        else:  # Assume European DD/MM/YYYY
                            day, month = first, second
                    elif first > 31:  # Year is first
                        year = first
                        month, day = second, third
                    else:
                        continue
                    
                    if 1 <= month <= 12 and 1 <= day <= 31 and 1900 <= year <= 2100:
                        return f'{year}-{month:02d}-{day:02d}'
                except (ValueError, IndexError):
                    continue
        
        return ''


def register_error_handlers(app):
    """Register error handlers."""
    
    @app.errorhandler(404)
    def not_found_error(error):
        from flask import render_template
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        from flask import render_template
        db.session.rollback()
        return render_template('errors/500.html'), 500
    
    @app.errorhandler(403)
    def forbidden_error(error):
        from flask import render_template
        return render_template('errors/403.html'), 403


# Application instance for running directly
app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
