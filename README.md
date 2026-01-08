# JPHN Transfer Management System - Web Application

## Department of Health Services, Kerala

### Overview
This is the web version of the JPHN Transfer Management System, converted from the PySide6 desktop application.

### Features
- **User Authentication** - Secure login system
- **Transfer Types** - Support for General Transfer and Regular Transfer
- **Cadre Management** - Add, edit, delete employee records
- **Vacancy Management** - Track vacancies by district
- **Transfer Applications** - Mark employees who have applied for transfer
- **Draft Transfer List** - Auto-fill vacancies based on preferences and priorities
- **Final Transfer List** - Confirm and finalize transfers
- **Export** - Export lists to CSV format

### Installation

1. **Create a virtual environment** (recommended):
```bash
python -m venv venv
venv\Scripts\activate  # On Windows
# source venv/bin/activate  # On Linux/Mac
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Run the application**:
```bash
python run.py
```

4. **Access the application**:
Open your browser and go to: http://localhost:5000

### Login Credentials
- **User ID**: revathy
- **Password**: 4117

### Project Structure
```
web_app/
├── app.py              # Main Flask application
├── config.py           # Configuration settings
├── run.py              # Application entry point
├── requirements.txt    # Python dependencies
├── README.md           # This file
├── templates/          # HTML templates
│   ├── base.html
│   ├── login.html
│   ├── select_transfer.html
│   ├── select_year.html
│   ├── select_month.html
│   ├── dashboard.html
│   ├── cadre_list.html
│   ├── employee_form.html
│   ├── vacancy.html
│   ├── application.html
│   ├── applied_employees.html
│   ├── draft_list.html
│   ├── final_list.html
│   └── error.html
└── static/
    ├── css/
    │   └── style.css   # Main stylesheet
    ├── js/
    │   └── script.js   # JavaScript functionality
    └── img/            # Images (optional)
```

### Database
The application connects to the same Supabase PostgreSQL database as the desktop version.

### Browser Support
- Chrome (recommended)
- Firefox
- Edge
- Safari

### Version
10.0 (Web Application)

### Technology Stack
- **Backend**: Flask (Python)
- **Database**: PostgreSQL (Supabase)
- **Frontend**: HTML5, CSS3, JavaScript
- **Icons**: Font Awesome
- **Fonts**: Google Fonts (Roboto)
