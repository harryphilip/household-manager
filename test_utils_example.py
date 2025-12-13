#!/usr/bin/env python
"""
Example script showing how to use utility functions.
Run this with: python test_utils_example.py
"""
import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'household_manager.settings')
django.setup()

# Now we can import Django models and utilities
from household.utils import (
    search_manual_online,
    extract_maintenance_info,
    extract_text_from_pdf
)
from household.models import Appliance


def test_search_manual():
    """Test searching for a manual online."""
    print("=" * 50)
    print("Testing: search_manual_online()")
    print("=" * 50)
    
    # Example search
    result = search_manual_online("Samsung", "RF28R7351SG", "Refrigerator")
    
    if result:
        print(f"✓ Found manual!")
        print(f"  Title: {result.get('title', 'N/A')}")
        print(f"  URL: {result.get('url', 'N/A')}")
    else:
        print("✗ No manual found")
    print()


def test_extract_maintenance():
    """Test extracting maintenance info from text."""
    print("=" * 50)
    print("Testing: extract_maintenance_info()")
    print("=" * 50)
    
    sample_text = """
    Clean the air filter monthly to ensure proper airflow and efficiency.
    Inspect the condenser coils quarterly for dust and debris buildup.
    Replace the water filter annually or when the filter indicator light comes on.
    Clean the door gasket weekly with a damp cloth.
    Defrost the freezer as needed when ice buildup exceeds 1/4 inch.
    """
    
    tasks = extract_maintenance_info(sample_text, "refrigerator")
    
    print(f"✓ Found {len(tasks)} maintenance tasks:\n")
    for i, task in enumerate(tasks, 1):
        print(f"Task {i}:")
        print(f"  Name: {task['task_name']}")
        print(f"  Frequency: {task['frequency']}")
        print(f"  Description: {task['description'][:100]}...")
        print()
    print()


def test_with_appliance():
    """Test utilities with an actual appliance from database."""
    print("=" * 50)
    print("Testing: With Database Appliance")
    print("=" * 50)
    
    # Get first appliance (or create one for testing)
    try:
        appliance = Appliance.objects.first()
        if not appliance:
            print("No appliances in database. Create one first!")
            return
        
        print(f"Testing with appliance: {appliance.name}")
        print(f"  Brand: {appliance.brand or 'N/A'}")
        print(f"  Model: {appliance.model_number or 'N/A'}")
        print()
        
        # Search for manual if brand/model exists
        if appliance.brand or appliance.model_number:
            print("Searching for manual...")
            result = search_manual_online(
                appliance.brand, 
                appliance.model_number, 
                appliance.name
            )
            if result:
                print(f"✓ Found: {result['url']}")
            else:
                print("✗ No manual found")
            print()
        
        # Extract from PDF if exists
        if appliance.manual_pdf:
            print("Extracting text from PDF...")
            pdf_file = appliance.manual_pdf.open('rb')
            text = extract_text_from_pdf(pdf_file)
            pdf_file.close()
            
            if text:
                print(f"✓ Extracted {len(text)} characters")
                print(f"  Preview: {text[:200]}...")
                
                # Extract maintenance tasks
                print("\nExtracting maintenance tasks...")
                tasks = extract_maintenance_info(text, appliance.appliance_type)
                print(f"✓ Found {len(tasks)} tasks")
            else:
                print("✗ Could not extract text")
        else:
            print("No PDF manual uploaded for this appliance")
            
    except Exception as e:
        print(f"Error: {e}")


if __name__ == '__main__':
    print("\n" + "=" * 50)
    print("Utility Functions Test Script")
    print("=" * 50 + "\n")
    
    # Run tests
    test_search_manual()
    test_extract_maintenance()
    test_with_appliance()
    
    print("=" * 50)
    print("Tests Complete!")
    print("=" * 50)

