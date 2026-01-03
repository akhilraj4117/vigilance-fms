from app import create_app
from extensions import db

app = create_app()

with app.app_context():
    # Fix report_asked_details sequence
    db.session.execute(db.text(
        "SELECT setval('report_asked_details_id_seq', COALESCE((SELECT MAX(id) FROM report_asked_details), 1), true)"
    ))
    db.session.commit()
    print("✓ Fixed report_asked_details sequence")
    
    # Also fix other common sequences
    tables = [
        'report_sought_details',
        'pr_entries', 
        'inquiry_details',
        'disciplinary_actions',
        'rti_applications',
        'court_cases'
    ]
    
    for table in tables:
        try:
            sql = f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), COALESCE((SELECT MAX(id) FROM {table}), 1), true)"
            db.session.execute(db.text(sql))
            print(f"✓ Fixed {table} sequence")
        except Exception as e:
            pass
    
    db.session.commit()
    print("\n✅ All sequences fixed! You can now save records.")
