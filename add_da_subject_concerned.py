"""Add subject and concerned columns to disciplinary_action_details table."""
from app import app, db
from sqlalchemy import text

with app.app_context():
    try:
        # Check if columns exist
        with db.engine.connect() as conn:
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'disciplinary_action_details'
            """))
            existing_columns = [row[0] for row in result]
            
            # Add subject column if not exists
            if 'subject' not in existing_columns:
                conn.execute(text("""
                    ALTER TABLE disciplinary_action_details 
                    ADD COLUMN subject TEXT
                """))
                conn.commit()
                print("✓ Added subject column")
            else:
                print("✓ subject column already exists")
            
            # Add concerned column if not exists
            if 'concerned' not in existing_columns:
                conn.execute(text("""
                    ALTER TABLE disciplinary_action_details 
                    ADD COLUMN concerned VARCHAR(200)
                """))
                conn.commit()
                print("✓ Added concerned column")
            else:
                print("✓ concerned column already exists")
                
        print("\n✓ Migration completed successfully!")
        
    except Exception as e:
        print(f"✗ Error during migration: {e}")
        db.session.rollback()
