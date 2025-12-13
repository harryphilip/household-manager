# How to Run Utility Functions

This guide shows you different ways to use the utility functions from `household/utils.py`.

## Available Utility Functions

1. `search_manual_online(brand, model_number, appliance_name)` - Search for manuals online
2. `download_pdf(url, appliance_name)` - Download PDF from URL
3. `extract_text_from_pdf(pdf_file)` - Extract text from PDF file
4. `extract_maintenance_info(text, appliance_type)` - Extract maintenance tasks from text
5. `extract_maintenance_with_ai(text, appliance_type)` - AI-powered extraction (optional)

## Method 1: Using Django Shell (Recommended for Testing)

Django shell gives you access to all Django models and utilities:

```bash
python manage.py shell
```

Then in the shell:

```python
# Import the utility functions
from household.utils import (
    search_manual_online, 
    download_pdf, 
    extract_text_from_pdf,
    extract_maintenance_info,
    extract_maintenance_with_ai
)
from household.models import Appliance

# Example 1: Search for a manual
result = search_manual_online("Samsung", "RF28R7351SG", "Refrigerator")
if result:
    print(f"Found manual: {result['title']}")
    print(f"URL: {result['url']}")
else:
    print("No manual found")

# Example 2: Get an appliance and search for its manual
appliance = Appliance.objects.get(pk=1)  # Replace 1 with your appliance ID
result = search_manual_online(appliance.brand, appliance.model_number, appliance.name)
print(result)

# Example 3: Extract text from an uploaded PDF
appliance = Appliance.objects.get(pk=1)
if appliance.manual_pdf:
    pdf_file = appliance.manual_pdf.open('rb')
    text = extract_text_from_pdf(pdf_file)
    pdf_file.close()
    print(f"Extracted {len(text)} characters")
    print(text[:500])  # Print first 500 characters

# Example 4: Extract maintenance tasks from text
text = "Clean the filter monthly. Inspect the coils quarterly."
tasks = extract_maintenance_info(text, "refrigerator")
for task in tasks:
    print(f"Task: {task['task_name']}")
    print(f"Frequency: {task['frequency']}")
    print(f"Description: {task['description']}")
    print("---")

# Example 5: Full workflow - Search, download, extract
appliance = Appliance.objects.get(pk=1)

# Step 1: Search
result = search_manual_online(appliance.brand, appliance.model_number, appliance.name)
if result:
    print(f"Found: {result['url']}")
    
    # Step 2: Download
    pdf_file = download_pdf(result['url'], appliance.name)
    if pdf_file:
        appliance.manual_pdf.save(pdf_file.name, pdf_file, save=True)
        print("PDF downloaded and saved!")
        
        # Step 3: Extract text
        pdf_file = appliance.manual_pdf.open('rb')
        text = extract_text_from_pdf(pdf_file)
        pdf_file.close()
        print(f"Extracted {len(text)} characters")
        
        # Step 4: Extract maintenance tasks
        tasks = extract_maintenance_with_ai(text, appliance.appliance_type)
        print(f"Found {len(tasks)} maintenance tasks")
        
        # Step 5: Create maintenance tasks
        from household.models import MaintenanceTask
        for task_data in tasks:
            task = MaintenanceTask.objects.create(
                appliance=appliance,
                task_name=task_data['task_name'],
                description=task_data.get('description', ''),
                frequency=task_data.get('frequency', 'monthly'),
                extracted_from_manual=True,
                is_active=True
            )
            print(f"Created task: {task.task_name}")
```

## Method 2: Through the Web Interface

The utility functions are already integrated into the web interface:

1. **Search for Manual**: 
   - Go to an appliance detail page
   - Click "🔍 Search for Manual Online" button
   - This calls `search_manual_online()` automatically

2. **Download Manual**:
   - After searching, click "⬇️ Download Manual"
   - This calls `download_pdf()` and saves it

3. **Extract Maintenance**:
   - Click "📋 Extract Maintenance Tasks"
   - This calls `extract_text_from_pdf()` and `extract_maintenance_with_ai()`

## Method 3: Create a Management Command

Create a custom Django management command for batch processing:

```bash
mkdir -p household/management/commands
touch household/management/__init__.py
touch household/management/commands/__init__.py
```

Then create `household/management/commands/process_manuals.py`:

```python
from django.core.management.base import BaseCommand
from household.models import Appliance
from household.utils import search_manual_online, download_pdf, extract_text_from_pdf, extract_maintenance_with_ai

class Command(BaseCommand):
    help = 'Search and process manuals for appliances without manuals'

    def handle(self, *args, **options):
        appliances = Appliance.objects.filter(manual_pdf__isnull=True)
        
        for appliance in appliances:
            if appliance.brand and appliance.model_number:
                self.stdout.write(f"Processing {appliance.name}...")
                
                # Search for manual
                result = search_manual_online(
                    appliance.brand, 
                    appliance.model_number, 
                    appliance.name
                )
                
                if result:
                    self.stdout.write(f"  Found: {result['url']}")
                    # Download and process...
                else:
                    self.stdout.write(f"  No manual found")
```

Run it with:
```bash
python manage.py process_manuals
```

## Method 4: Create a Standalone Script

Create a script file `test_utils.py` in the project root:

```python
#!/usr/bin/env python
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'household_manager.settings')
django.setup()

# Now import your utilities
from household.utils import search_manual_online, extract_maintenance_info

# Test the functions
result = search_manual_online("Whirlpool", "WED4815EW", "Dryer")
print(result)

text = "Clean the lint filter after every use. Inspect the vent monthly."
tasks = extract_maintenance_info(text, "dryer")
for task in tasks:
    print(task)
```

Run it with:
```bash
python test_utils.py
```

## Method 5: Using Python Interactively

You can also test functions directly in Python (but you need Django setup):

```python
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'household_manager.settings')
django.setup()

from household.utils import search_manual_online

# Test search
result = search_manual_online("LG", "WM3900HWA", "Washer")
print(result)
```

## Common Use Cases

### Test Manual Search
```python
python manage.py shell
>>> from household.utils import search_manual_online
>>> result = search_manual_online("Samsung", "RF28R7351SG", "Refrigerator")
>>> print(result)
```

### Extract Text from Existing PDF
```python
python manage.py shell
>>> from household.utils import extract_text_from_pdf
>>> from household.models import Appliance
>>> appliance = Appliance.objects.get(pk=1)
>>> pdf_file = appliance.manual_pdf.open('rb')
>>> text = extract_text_from_pdf(pdf_file)
>>> print(text[:1000])  # First 1000 characters
```

### Test Maintenance Extraction
```python
python manage.py shell
>>> from household.utils import extract_maintenance_info
>>> sample_text = """
... Clean the air filter monthly to ensure proper airflow.
... Inspect the coils quarterly for dust buildup.
... Replace the water filter annually.
... """
>>> tasks = extract_maintenance_info(sample_text, "refrigerator")
>>> for task in tasks:
...     print(f"{task['task_name']} - {task['frequency']}")
```

## Troubleshooting

### Import Errors
If you get import errors, make sure:
1. You're in the project directory
2. Virtual environment is activated (if using one)
3. All dependencies are installed: `pip install -r requirements.txt`

### Django Not Set Up
When using Django shell or management commands, Django is automatically set up.
For standalone scripts, you need:
```python
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'household_manager.settings')
django.setup()
```

### PDF File Issues
When working with PDF files:
- Make sure the file is opened in binary mode: `open('rb')`
- Reset file pointer: `pdf_file.seek(0)` before reading
- Close files after use: `pdf_file.close()`

## Quick Reference

| Function | Purpose | Returns |
|----------|---------|---------|
| `search_manual_online()` | Search Google for PDF manuals | Dict with 'url' and 'title' or None |
| `download_pdf()` | Download PDF from URL | Django ContentFile or None |
| `extract_text_from_pdf()` | Extract text from PDF | String (text content) |
| `extract_maintenance_info()` | Parse maintenance tasks from text | List of task dictionaries |
| `extract_maintenance_with_ai()` | AI-powered extraction | List of task dictionaries |

