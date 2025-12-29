"""
Add designation and institution fields to complaint_details table.
Run this script to update the database schema.
Works with both SQLite (local) and PostgreSQL (production).
"""
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app, db
from sqlalchemy import text

def add_complaint_fields():
    app = create_app()
    
    with app.app_context():
        print("Checking database schema for complaint_details table...")
        
        try:
            # Check which fields exist
            result = db.session.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'complaint_details'
            """))
            existing_columns = [row[0] for row in result]
            
            fields_to_add = []
            if 'plaintiff_designation' not in existing_columns:
                fields_to_add.append('plaintiff_designation')
            if 'plaintiff_institution' not in existing_columns:
                fields_to_add.append('plaintiff_institution')
            if 'respondent_designation' not in existing_columns:
                fields_to_add.append('respondent_designation')
            if 'respondent_institution' not in existing_columns:
                fields_to_add.append('respondent_institution')
            
            if not fields_to_add:
                print("✅ All complaint fields already exist. No changes needed.")
                return
            
            print(f"Adding {len(fields_to_add)} new fields to complaint_details table...")
            
            for field_name in fields_to_add:
                sql = f"ALTER TABLE complaint_details ADD COLUMN {field_name} VARCHAR(200)"
                db.session.execute(text(sql))
                print(f"  ✓ Added {field_name}")
            
            db.session.commit()
            print("\n✅ Database updated successfully!")
            print("\nNew fields added:")
            for field in fields_to_add:
                print(f"  - {field}")
            
        except Exception as e:
            print(f"❌ Error updating database: {e}")
            db.session.rollback()
            
            # For SQLite, information_schema doesn't exist, so try PRAGMA
            try:
                print("\nTrying SQLite approach...")
                result = db.session.execute(text("PRAGMA table_info(complaint_details)"))
                existing_columns = [row[1] for row in result]
                
                fields_to_add = []
                if 'plaintiff_designation' not in existing_columns:
                    fields_to_add.append('plaintiff_designation')
                if 'plaintiff_institution' not in existing_columns:
                    fields_to_add.append('plaintiff_institution')
                if 'respondent_designation' not in existing_columns:
                    fields_to_add.append('respondent_designation')
                if 'respondent_institution' not in existing_columns:
                    fields_to_add.append('respondent_institution')
                
                if not fields_to_add:
                    print("✅ All complaint fields already exist. No changes needed.")
                    return
                
                for field_name in fields_to_add:
                    sql = f"ALTER TABLE complaint_details ADD COLUMN {field_name} VARCHAR(200)"
                    db.session.execute(text(sql))
                    print(f"  ✓ Added {field_name}")
                
                db.session.commit()
                print("\n✅ Database updated successfully!")
                
            except Exception as e2:
                print(f"❌ Error with SQLite approach: {e2}")
                db.session.rollback()

if __name__ == '__main__':
    add_complaint_fields()
