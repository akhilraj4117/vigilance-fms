"""
JPHN Transfer Management System - Web Application
Run this file to start the Flask development server
"""
from app import app, db

if __name__ == '__main__':
    # Create tables on startup
    with app.app_context():
        # Initialize the database connection
        print("Starting JPHN Transfer Web Application...")
        print("Database connected to Supabase PostgreSQL")
        
    # Run the Flask development server
    app.run(
        host='0.0.0.0',  # Allow external connections
        port=5000,
        debug=True,
        use_reloader=True
    )
