# Vigilance File Management System - Web Application

A comprehensive Flask web application for managing vigilance-related files, disciplinary actions, RTI applications, and more for the District Medical Office (Health), Thiruvananthapuram.

## Features

- **File Management**: Create, view, edit, and close vigilance files with categorization
- **Disciplinary Actions**: Track disciplinary proceedings against employees
- **RTI Applications**: Manage Right to Information applications and appeals
- **Court Cases**: Track ongoing court cases
- **Inquiries**: Manage inquiry proceedings
- **Employee Database**: Maintain employee master data
- **Institution Database**: Maintain institution master data
- **Reports**: Generate various reports with export functionality
- **User Management**: Role-based access control (Admin/Guest)

## Technology Stack

- **Backend**: Python Flask
- **Database**: PostgreSQL (production) / SQLite (development)
- **ORM**: SQLAlchemy
- **Authentication**: Flask-Login
- **Frontend**: Bootstrap 5, Bootstrap Icons
- **Deployment**: Render.com

## Local Development Setup

1. **Clone the repository**
   ```bash
   cd "Web App Files"
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   # source venv/bin/activate  # Linux/Mac
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set environment variables**
   Create a `.env` file:
   ```
   FLASK_ENV=development
   SECRET_KEY=your-secret-key-here
   DATABASE_URL=sqlite:///vigilance.db
   ```

5. **Run the application**
   ```bash
   python app.py
   ```

6. **Access the application**
   Open http://localhost:5000 in your browser

## Default Credentials

- **Admin User**: 
  - Username: `akhil`
  - Password: `876123`
- **Guest User**:
  - Username: `guest`
  - Password: `1234`

> ⚠️ **Important**: Change default passwords after first login!

## Deployment to Render.com

### Automatic Deployment

1. Push your code to GitHub
2. Connect your GitHub repository to Render.com
3. Render will automatically detect the `render.yaml` and deploy

### Manual Deployment

1. Create a new Web Service on Render.com
2. Connect your GitHub repository
3. Configure:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
4. Add environment variables:
   - `FLASK_ENV`: production
   - `SECRET_KEY`: (generate a secure key)
   - `DATABASE_URL`: (PostgreSQL connection string)
5. Deploy

## Project Structure

```
Web App Files/
├── app.py                 # Main Flask application
├── config.py              # Configuration settings
├── models.py              # SQLAlchemy database models
├── requirements.txt       # Python dependencies
├── render.yaml           # Render.com deployment config
├── routes/               # Route blueprints
│   ├── __init__.py
│   ├── auth.py           # Authentication routes
│   ├── main.py           # Main/dashboard routes
│   ├── files.py          # File management routes
│   ├── disciplinary.py   # Disciplinary action routes
│   ├── rti.py            # RTI application routes
│   ├── institutions.py   # Institution routes
│   ├── employees.py      # Employee routes
│   ├── reports.py        # Report routes
│   └── api.py            # API endpoints
├── templates/            # Jinja2 HTML templates
│   ├── base.html         # Base template
│   ├── auth/             # Auth templates
│   ├── main/             # Main templates
│   ├── files/            # File templates
│   └── ...
└── static/               # Static files
    ├── css/
    │   └── style.css     # Custom styles
    └── js/
        └── main.js       # Custom JavaScript
```

## User Roles

### Administrator
- Full access to all features
- Can create, edit, delete all records
- Can close and reopen files
- Can manage users

### Guest
- Read-only access
- Can create new records
- Cannot delete records
- Cannot close/reopen files
- Cannot manage users

## API Endpoints

The application provides RESTful API endpoints for integration:

- `GET /api/health` - Health check
- `GET /api/stats` - System statistics
- `GET /api/files` - List files
- `GET /api/files/<file_number>` - Get file details
- `GET /api/employees` - List employees
- `GET /api/institutions` - List institutions
- `GET /api/search?q=<query>` - Global search

## License

This project is developed for the District Medical Office (Health), Thiruvananthapuram.

## Support

For technical support, please contact the system administrator.
