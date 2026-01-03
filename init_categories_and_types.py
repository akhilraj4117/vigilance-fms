"""
Initialize the database with default categories and file types.
Run this once after creating the new tables.
"""
import os
os.environ['FLASK_ENV'] = 'development'  # Use local SQLite database

from app import create_app
from extensions import db
from models import FileType, Category

app = create_app()

with app.app_context():
    # Create tables
    db.create_all()
    
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
            print(f"✓ Added file type: {ft_name}")
    
    # Add categories if they don't exist
    for cat_name in default_categories:
        if not Category.query.filter_by(name=cat_name).first():
            cat = Category(name=cat_name)
            db.session.add(cat)
            print(f"✓ Added category: {cat_name}")
    
    db.session.commit()
    print("\n✅ Database initialized with default categories and file types!")
    print(f"Total file types: {FileType.query.count()}")
    print(f"Total categories: {Category.query.count()}")
