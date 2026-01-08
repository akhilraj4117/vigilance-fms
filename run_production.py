"""
JPHN Transfer Management System - Production Server
Run this file to start the production server accessible from any computer on the network
"""
from waitress import serve
from app import app

if __name__ == '__main__':
    print("=" * 60)
    print("JPHN Transfer Web Application - Production Server")
    print("=" * 60)
    print()
    print("Server starting on all network interfaces...")
    print()
    print("Access from THIS computer:  http://localhost:5000")
    print("Access from OTHER computers: http://<YOUR-IP>:5000")
    print()
    print("To find your IP, run: ipconfig")
    print()
    print("Press Ctrl+C to stop the server")
    print("=" * 60)
    
    # Serve on all interfaces, port 5000
    serve(app, host='0.0.0.0', port=5000, threads=4)
