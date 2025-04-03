# TakeCare
CRM for Doctor-Patient Relations

## Overview
**TakeCare** is designed to simplify and streamline interactions between doctors and patients. This system will offer appointment scheduling, patient data management, and communication tools in a single, efficient platform.

## Technologies

### Backend
- **Python** 
- **Django** 
- **PostgreSQL**

### Frontend
- **HTML** 
- **CSS** 
- **JavaScript**

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
