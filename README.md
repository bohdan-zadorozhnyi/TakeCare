# TakeCare
CRM for Doctor-Patient Relations

## Overview
**TakeCare** is designed to simplify and streamline interactions between doctors and patients. This system will offer appointment scheduling, patient data management, and communication tools in a single, efficient platform.

## Technologies

### Backend
- **Python** 
- **Django** 
- **PostgreSQL**
- **Redis**

### Frontend
- **HTML** 
- **CSS** 
- **JavaScript**


## Prerequisites

### For Docker Setup
- Docker and Docker Compose
- Git

### For Local Setup
- Python 3.12+
- PostgreSQL 14+
- Redis 7+
- Git

## Setup Instructions

### Using Docker (Recommended)

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/TakeCare.git
   cd TakeCare
   ```

2. Start the services using Docker Compose:
   ```bash
   docker compose up -d
   ```

3. The application will be available at http://localhost:8000

Default superuser credentials:
- Email: admin@example.com
- Password: admin123

### Local Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/TakeCare.git
   cd TakeCare
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up PostgreSQL:
   - Create a database named 'takecare'
   - Create a user 'postgres' with password '12345'
   - Grant all privileges on the database to the user

5. Set up environment variables:
   ```bash
   export POSTGRES_DB=takecare
   export POSTGRES_USER=postgres
   export POSTGRES_PASSWORD=12345
   export POSTGRES_HOST=localhost
   export REDIS_HOST=localhost
   export DJANGO_DEBUG=True
   ```

6. Run database migrations:
   ```bash
   python manage.py migrate
   ```

7. Create a superuser:
   ```bash
   python manage.py createsuperuser
   ```

8. Start the Redis server

9. Run the development server:
   ```bash
   python manage.py runserver
   ```

10. The application will be available at http://localhost:8000

## Key Features
- Patient-Doctor appointment scheduling
- Real-time chat between patients and doctors
- Medical records management
- Prescription management
- Referral system
- Article publishing system
- Notification system

## Conventions

### Git Branching
- **main** – Production-ready branch
- **develop** – Integration branch for features in progress
- **feature/** – Branches for new features
- **fix/** – Branches for bug fixes
- **hotfix/** – Branches for urgent fixes on main (if needed)

### Commits
- Start each commit message with an uppercase letter.
- Use concise yet descriptive messages (e.g., *"Add user authentication flow"*).

### Django Project Naming Conventions 
- **Apps**: lowercase, plural (e.g., users, appointments)
- **Models**: PascalCase (e.g., UserProfile)
- **Templates**: lowercase with underscores (e.g., user_profile.html)
- **Static Files**: lowercase with underscores (e.g., user_default_image.png).

### Jira Usage
- **Epics** are referred to as **Features** (e.g., “Feature: User Authentication”)
- **Issues** are broken down as **Stories** under these features
- For increased detail, **Tasks** and **Sub-tasks** fields might be incorporated.

### Additional Conventions
- Follow PEP 8 guidelines for Python code styling
- Use clear docstrings for functions and classes
- Maintain a consistent naming convention for HTML/CSS/JS files (e.g., snake_case for CSS, camelCase for JS)

## Schedule
- **Sprints**: We will have two-week sprints to plan, develop, and review features
- **Weeklies**: Weekly stand-ups/meetings to coordinate tasks and address blockers
- **Management**: We will use Jira to manage and track our backlog and sprint tasks
- **Methodology**: Our team will work in **Scrum**, adapting as needed based on project requirements
