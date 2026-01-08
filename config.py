"""
Database Configuration for JPHN Transfer Web App
Supabase PostgreSQL Configuration
"""
import os
from urllib.parse import quote_plus

class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'jphn-transfer-secret-key-2025'
    
    # Database Configuration - PostgreSQL (Supabase)
    # Using port 6543 (Transaction Pooler) instead of 5432 to bypass ISP blocking
    DB_HOST = 'aws-0-ap-south-1.pooler.supabase.com'
    DB_PORT = 6543  # Transaction pooler port (use this if 5432 is blocked)
    DB_NAME = 'postgres'
    DB_USER = 'postgres.xyspjqfyxiyrowvxyqad'
    DB_PASSWORD = 'JPHNTransferDB@123'
    
    # Check for DATABASE_URL environment variable first (for Render deployment)
    # Use postgresql+psycopg:// for psycopg3 compatibility
    if os.environ.get('DATABASE_URL'):
        # Replace postgres:// with postgresql+psycopg:// for psycopg3
        _db_url = os.environ.get('DATABASE_URL')
        if _db_url.startswith('postgres://'):
            _db_url = _db_url.replace('postgres://', 'postgresql+psycopg://', 1)
        elif _db_url.startswith('postgresql://'):
            _db_url = _db_url.replace('postgresql://', 'postgresql+psycopg://', 1)
        SQLALCHEMY_DATABASE_URI = _db_url
    else:
        # URL-encode the password to handle special characters like @
        SQLALCHEMY_DATABASE_URI = (
            f"postgresql+psycopg://{DB_USER}:{quote_plus(DB_PASSWORD)}@"
            f"{DB_HOST}:{DB_PORT}/{DB_NAME}?sslmode=require"
        )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 5,
        'pool_recycle': 300,
        'pool_pre_ping': True,
        'connect_args': {
            'connect_timeout': 30,
            'sslmode': 'require'
        }
    }
    
    # Valid users for authentication
    VALID_USERS = {
        'revathy': '4117'
    }
    
    # Districts in Kerala
    DISTRICTS = [
        "Thiruvananthapuram", "Kollam", "Pathanamthitta", "Alappuzha",
        "Kottayam", "Idukki", "Ernakulam", "Thrissur", "Palakkad",
        "Malappuram", "Kozhikode", "Wayanad", "Kannur", "Kasaragod"
    ]
    
    # Nearby districts mapping (for against transfers)
    NEARBY_DISTRICTS = {
        "Thiruvananthapuram": ["Kollam", "Pathanamthitta", "Kottayam"],
        "Kollam": ["Thiruvananthapuram", "Pathanamthitta", "Alappuzha"],
        "Pathanamthitta": ["Kollam", "Alappuzha", "Kottayam", "Idukki"],
        "Alappuzha": ["Kollam", "Pathanamthitta", "Kottayam", "Ernakulam"],
        "Kottayam": ["Pathanamthitta", "Alappuzha", "Idukki", "Ernakulam"],
        "Idukki": ["Pathanamthitta", "Kottayam", "Ernakulam", "Thrissur"],
        "Ernakulam": ["Alappuzha", "Kottayam", "Idukki", "Thrissur"],
        "Thrissur": ["Ernakulam", "Idukki", "Palakkad", "Malappuram"],
        "Palakkad": ["Thrissur", "Malappuram"],
        "Malappuram": ["Thrissur", "Palakkad", "Kozhikode", "Wayanad"],
        "Kozhikode": ["Malappuram", "Wayanad", "Kannur"],
        "Wayanad": ["Malappuram", "Kozhikode", "Kannur"],
        "Kannur": ["Kozhikode", "Wayanad", "Kasaragod"],
        "Kasaragod": ["Kannur"]
    }
    
    # Months list
    MONTHS = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ]


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
