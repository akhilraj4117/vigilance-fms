"""
Routes package initialization.
"""
from routes.auth import auth_bp
from routes.main import main_bp
from routes.files import files_bp
from routes.disciplinary import disciplinary_bp
from routes.rti import rti_bp
from routes.institutions import institutions_bp
from routes.employees import employees_bp
from routes.reports import reports_bp
from routes.api import api_bp

__all__ = [
    'auth_bp',
    'main_bp',
    'files_bp',
    'disciplinary_bp',
    'rti_bp',
    'institutions_bp',
    'employees_bp',
    'reports_bp',
    'api_bp'
]
