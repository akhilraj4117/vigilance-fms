"""
Configuration settings for the Flask application.
"""
import os
from datetime import timedelta


def add_prepare_threshold(url):
    """Add prepare_threshold=0 to database URL for psycopg3 pooled connections."""
    if not url:
        return url
    # Add prepare_threshold=0 to disable prepared statements (required for pooled connections)
    if '?' in url:
        return url + '&prepare_threshold=0'
    else:
        return url + '?prepare_threshold=0'


class Config:
    """Base configuration class."""
    
    # Secret key for session management and CSRF protection
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-change-in-production'
    
    # Database configuration - Supabase PostgreSQL (Session Pooler - IPv4 compatible)
    # Add prepare_threshold=0 to disable prepared statements for pooled connections
    SUPABASE_DB_URL = 'postgresql+psycopg://postgres.qkhpacqsztvpnkrfmwgz:Revathyr%40j6123@aws-1-ap-southeast-2.pooler.supabase.com:6543/postgres?prepare_threshold=0'
    SQLALCHEMY_DATABASE_URI = add_prepare_threshold(os.environ.get('DATABASE_URL')) or SUPABASE_DB_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # SSL mode for PostgreSQL connections
    SQLALCHEMY_ENGINE_OPTIONS = {
        'connect_args': {
            'sslmode': 'require'
        }
    }
    
    # Session configuration
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    
    # File upload configuration
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # Pagination
    ITEMS_PER_PAGE = 20
    
    # Application settings
    APP_NAME = "Vigilance File Management System"
    ORGANIZATION = "District Medical Office (Health), Thiruvananthapuram"


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    

class ProductionConfig(Config):
    """Production configuration for Render.com deployment."""
    DEBUG = False
    
    # Use DATABASE_URL from environment or fall back to Supabase
    _raw_db_url = os.environ.get('DATABASE_URL') or Config.SUPABASE_DB_URL
    
    # Fix for PostgreSQL URL format (Render uses postgres://)
    if _raw_db_url:
        if _raw_db_url.startswith('postgres://'):
            _raw_db_url = _raw_db_url.replace('postgres://', 'postgresql+psycopg://', 1)
        elif _raw_db_url.startswith('postgresql://') and '+psycopg' not in _raw_db_url:
            _raw_db_url = _raw_db_url.replace('postgresql://', 'postgresql+psycopg://', 1)
    
    # Add prepare_threshold for pooled connections
    SQLALCHEMY_DATABASE_URI = add_prepare_threshold(_raw_db_url)


class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
