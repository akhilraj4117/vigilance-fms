"""
Flask extensions initialization.
This file exists to avoid circular imports.
"""
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from sqlalchemy import event

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()


def configure_db_for_pooling(app):
    """Configure database connection for pooled connections (Supabase/PgBouncer).
    
    This disables prepared statements which cause conflicts with connection pooling.
    """
    @event.listens_for(db.engine, "connect")
    def set_prepare_threshold(dbapi_connection, connection_record):
        """Disable prepared statements for psycopg3 connections."""
        try:
            # For psycopg3, set prepare_threshold to 0 to disable prepared statements
            dbapi_connection.prepare_threshold = 0
        except AttributeError:
            # Not a psycopg3 connection, ignore
            pass
