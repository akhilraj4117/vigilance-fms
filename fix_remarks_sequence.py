"""
Fix remarks_entries sequence in PostgreSQL database.
This script resets the auto-increment sequence to the correct value.
"""
from app import create_app
from extensions import db
from sqlalchemy import text

app = create_app()

with app.app_context():
    try:
        # Get the maximum ID from the remarks_entries table
        result = db.session.execute(text("SELECT MAX(id) FROM remarks_entries")).fetchone()
        max_id = result[0] if result[0] else 0
        
        print(f"Current maximum ID in remarks_entries: {max_id}")
        
        # Reset the sequence to start from max_id + 1
        next_id = max_id + 1
        db.session.execute(text(f"SELECT setval('remarks_entries_id_seq', {next_id}, false)"))
        db.session.commit()
        
        print(f"✓ Successfully reset remarks_entries sequence to start from {next_id}")
        
        # Verify the fix
        result = db.session.execute(text("SELECT last_value FROM remarks_entries_id_seq")).fetchone()
        print(f"✓ Sequence current value: {result[0]}")
        
    except Exception as e:
        print(f"✗ Error fixing sequence: {e}")
        db.session.rollback()
