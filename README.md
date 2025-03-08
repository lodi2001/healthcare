# Healthcare Application

A comprehensive healthcare application that integrates electronic health records (EHR) and genomic data, providing user-specific dashboards for healthcare providers, patients, companies, researchers, and government officials.

## Features

- **User Authentication**: Registration, login, and user type selection
- **Role-Based Dashboards**: Tailored dashboards for different user types
- **Electronic Health Records (EHR)**: Management of patient health information
- **Genomic Data**: Storage and analysis of patient genomic information
- **Clinical Services**: Access to various clinical services
- **Genomic Services**: Access to genomic analysis services
- **Reports**: Creation, viewing, and management of patient reports

## User Types

1. **Healthcare Providers**: Doctors, nurses, and other medical professionals
2. **Patients**: Individuals receiving healthcare services
3. **Companies**: Healthcare organizations and insurance companies
4. **Researchers**: Medical and genomic researchers
5. **Government Officials**: Public health and regulatory authorities

## Technology Stack

- **Backend**: Django, Django REST Framework
- **Frontend**: HTML, CSS, JavaScript, Bootstrap 5
- **Database**: SQLite (development), PostgreSQL (production)
- **Authentication**: Django's built-in authentication system

## Setup Instructions

### Prerequisites

- Python 3.8+
- pip (Python package manager)
- virtualenv (recommended)

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/healthcare-app.git
   cd healthcare-app
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Set up environment variables (create a `.env` file in the project root):
   ```
   SECRET_KEY=your_secret_key
   DEBUG=True
   ALLOWED_HOSTS=localhost,127.0.0.1
   ```

5. Run migrations:
   ```
   python manage.py migrate
   ```

6. Create a superuser:
   ```
   python manage.py createsuperuser
   ```

7. Run the development server:
   ```
   python manage.py runserver
   ```

8. Access the application at http://127.0.0.1:8000/

## Project Structure

```
Healthcare/
├── apps/
│   ├── core/                  # Core functionality
│   ├── dashboard/             # Dashboard views and logic
│   ├── ehr/                   # Electronic Health Records
│   ├── genomics/              # Genomic data management
│   ├── reports/               # Report generation and management
│   ├── services/              # Clinical and genomic services
│   └── users/                 # User authentication and profiles
├── healthcare_project/        # Project settings
├── static/                    # Static files (CSS, JS, images)
├── templates/                 # HTML templates
│   ├── base/                  # Base templates
│   ├── dashboard/             # Dashboard templates
│   ├── reports/               # Report templates
│   ├── services/              # Services templates
│   └── users/                 # Authentication templates
├── manage.py                  # Django management script
└── requirements.txt           # Project dependencies
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Django community for the excellent web framework
- Bootstrap team for the responsive UI components
