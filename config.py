"""
Database Configuration for JPHN Transfer Web App
Supabase PostgreSQL Configuration
"""
import os
from datetime import timedelta

class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Database - Use PostgreSQL URL from environment or SQLite for local
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///jphn_transfer.db'
    
    # Fix for postgres:// vs postgresql://
    if SQLALCHEMY_DATABASE_URI and SQLALCHEMY_DATABASE_URI.startswith('postgres://'):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace('postgres://', 'postgresql://', 1)
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,      # Test connections before using
        'pool_recycle': 120,        # Recycle connections every 2 minutes (Supabase drops idle)
        'pool_size': 3,             # Slightly more connections for free tier
        'max_overflow': 2,          # Allow 2 extra connections under load
        'pool_timeout': 15,         # Don't wait too long for connections
        'pool_reset_on_return': 'rollback',  # Clean up connections properly
        'connect_args': {
            'connect_timeout': 8,   # Faster connection timeout
            'options': '-c statement_timeout=20000',  # 20 second query timeout
            'keepalives': 1,
            'keepalives_idle': 20,   # Send keepalive earlier
            'keepalives_interval': 5,
            'keepalives_count': 3
        }
    }
    
    # Session configuration
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    
    # Districts of Kerala
    DISTRICTS = [
        'Thiruvananthapuram', 'Kollam', 'Pathanamthitta', 'Alappuzha',
        'Kottayam', 'Idukki', 'Ernakulam', 'Thrissur', 'Palakkad',
        'Malappuram', 'Kozhikode', 'Wayanad', 'Kannur', 'Kasaragod'
    ]
    
    # Nearby districts mapping for against transfers
    NEARBY_DISTRICTS = {
        'Thiruvananthapuram': ['Kollam', 'Pathanamthitta'],
        'Kollam': ['Thiruvananthapuram', 'Pathanamthitta', 'Alappuzha'],
        'Pathanamthitta': ['Kollam', 'Alappuzha', 'Kottayam', 'Idukki'],
        'Alappuzha': ['Kollam', 'Pathanamthitta', 'Kottayam', 'Ernakulam'],
        'Kottayam': ['Pathanamthitta', 'Alappuzha', 'Idukki', 'Ernakulam'],
        'Idukki': ['Pathanamthitta', 'Kottayam', 'Ernakulam', 'Thrissur'],
        'Ernakulam': ['Alappuzha', 'Kottayam', 'Idukki', 'Thrissur'],
        'Thrissur': ['Ernakulam', 'Idukki', 'Palakkad', 'Malappuram'],
        'Palakkad': ['Thrissur', 'Malappuram', 'Coimbatore'],
        'Malappuram': ['Thrissur', 'Palakkad', 'Kozhikode', 'Wayanad'],
        'Kozhikode': ['Malappuram', 'Wayanad', 'Kannur'],
        'Wayanad': ['Malappuram', 'Kozhikode', 'Kannur', 'Mysore'],
        'Kannur': ['Kozhikode', 'Wayanad', 'Kasaragod'],
        'Kasaragod': ['Kannur', 'Mangalore']
    }
    
    # Months
    MONTHS = ['January', 'February', 'March', 'April', 'May', 'June',
              'July', 'August', 'September', 'October', 'November', 'December']
    
    # Valid users (change in production!)
    VALID_USERS = {
        'revathy': '4117'
    }


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
