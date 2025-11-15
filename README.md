# Export Dispatch System

A Django-based dispatch management system for export operations.

## Features
- Create/edit dispatch notes
- Generate loading sheets & pallet labels
- Role-based access (admin vs. staff)
- Customer & product management
- Reporting (by customer, product, status)
- Mobile-responsive design

## Setup
1. Clone the repo
2. Create virtual environment: `python -m venv .venv`
3. Install dependencies: `pip install -r requirements.txt`
4. Run migrations: `python manage.py migrate`
5. Start server: `python manage.py runserver 0.0.0.0:8000`

## Access
- PC: http://127.0.0.1:8000
- Mobile (same Wi-Fi): http://[YOUR_PC_IP]:8000