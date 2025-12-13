# Household Manager

A Django-based web application for managing household details including rooms, appliances, vendors, and past invoices.

## Features

- **Rooms Management**: Track rooms in your household with details like type, floor, and square footage
- **Appliances Tracking**: Manage appliances with purchase dates, warranties, and room assignments
- **Vendor Management**: Store vendor information including contact details and service types
- **Invoice Tracking**: Keep records of past invoices with payment status and file attachments

## Installation

1. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
   - Copy `.env.example` to `.env`:
     ```bash
     cp .env.example .env
     ```
   - Generate a Django secret key:
     ```bash
     python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
     ```
   - Edit `.env` and replace `your-secret-key-here-change-this-in-production` with the generated key

4. Run migrations:
```bash
python manage.py makemigrations
python manage.py migrate
```

4. Create a superuser (optional, for admin access):
```bash
python manage.py createsuperuser
```

5. Run the development server:
```bash
python manage.py runserver
```

6. Open your browser and navigate to:
   - Main application: http://127.0.0.1:8000/
   - Admin panel: http://127.0.0.1:8000/admin/

## Project Structure

```
household_manager/
├── household_manager/     # Project settings
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── household/            # Main application
│   ├── models.py         # Data models
│   ├── views.py          # View logic
│   ├── urls.py           # URL routing
│   ├── admin.py          # Admin configuration
│   └── templates/        # HTML templates
├── manage.py
└── requirements.txt
```

## Usage

### Rooms
- Add rooms to your household
- Assign appliances to rooms
- Track room details like floor and square footage

### Appliances
- Register appliances with brand, model, and serial numbers
- Track purchase dates and warranty information
- Link appliances to rooms
- View related invoices

### Vendors
- Store vendor contact information
- Categorize vendors by service type
- Track invoices from each vendor

### Invoices
- Record invoice details including amounts and dates
- Track payment status
- Upload invoice files
- Link invoices to vendors and appliances

## Admin Panel

Access the Django admin panel at `/admin/` to manage all data with a user-friendly interface. You'll need to create a superuser account first using `python manage.py createsuperuser`.

## Development

This is a template project. You can customize it by:
- Modifying models in `household/models.py`
- Adding new views in `household/views.py`
- Customizing templates in `household/templates/`
- Adding new features and functionality

## License

This is a template project for personal use.


