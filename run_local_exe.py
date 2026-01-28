"""
JPHN Transfer Management System - Local Executable
Runs the web app locally connecting to Supabase PostgreSQL
Double-click to start, then open http://localhost:5000 in browser
"""
import os
import sys
import webbrowser
import threading
import time
import socket

# Set environment for local mode
os.environ['FLASK_ENV'] = 'development'

# Supabase PostgreSQL connection - MUST be set BEFORE importing app
os.environ['DATABASE_URL'] = 'postgresql://postgres.qkhpacqsztvpnkrfmwgz:Revathyr@j6123@aws-1-ap-south-1.pooler.supabase.com:6543/postgres'

def find_free_port(start_port=5000):
    """Find an available port starting from start_port"""
    port = start_port
    while port < start_port + 100:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(('127.0.0.1', port))
            sock.close()
            return port
        except OSError:
            port += 1
    return start_port

def open_browser(port):
    """Open browser after a short delay"""
    time.sleep(2)
    webbrowser.open(f'http://localhost:{port}')

def get_local_ip():
    """Get the local IP address for LAN access"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

if __name__ == '__main__':
    print("=" * 60)
    print("  JPHN Transfer Management System - Local Server")
    print("=" * 60)
    print()
    
    # Import Flask app
    try:
        from app import app
        print("[OK] Flask app loaded successfully")
    except Exception as e:
        print(f"[ERROR] Failed to load app: {e}")
        input("\nPress Enter to exit...")
        sys.exit(1)
    
    # Find available port
    port = find_free_port(5000)
    local_ip = get_local_ip()
    
    print()
    print("Starting server...")
    print("-" * 60)
    print(f"  Local access:   http://localhost:{port}")
    print(f"  LAN access:     http://{local_ip}:{port}")
    print("-" * 60)
    print()
    print("Press Ctrl+C to stop the server")
    print()
    
    # Open browser automatically
    browser_thread = threading.Thread(target=open_browser, args=(port,), daemon=True)
    browser_thread.start()
    
    try:
        # Run Flask app (production-like with no reloader for exe)
        app.run(
            host='0.0.0.0',  # Allow LAN access
            port=port,
            debug=False,     # No debug mode for exe
            use_reloader=False,  # Must be False for PyInstaller
            threaded=True
        )
    except KeyboardInterrupt:
        print("\nServer stopped.")
    except Exception as e:
        print(f"\n[ERROR] Server error: {e}")
        input("\nPress Enter to exit...")
