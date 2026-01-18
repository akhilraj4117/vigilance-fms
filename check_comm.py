from app import app
from models import db, Communication

with app.app_context():
    comms = Communication.query.filter_by(file_number='DMOH-TVM/3089/2024-A6').all()
    print(f'Found {len(comms)} communications')
    for c in comms:
        print(f'ID: {c.id}')
        print(f'  Name: {repr(c.communication_name)}')
        print(f'  Title: {repr(c.document_title)}')
        print(f'  Content len: {len(c.content) if c.content else 0}')
        print()
