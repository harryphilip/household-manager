# Testing Guide

This document explains how to run and write tests for the Household Manager application.

## Running Tests

### Run All Tests
```bash
python manage.py test
```

### Run Specific Test File
```bash
python manage.py test household.tests.test_models
python manage.py test household.tests.test_views
python manage.py test household.tests.test_utils
```

### Run Specific Test Class
```bash
python manage.py test household.tests.test_models.RoomModelTest
```

### Run Specific Test Method
```bash
python manage.py test household.tests.test_models.RoomModelTest.test_room_creation
```

### Run with Verbose Output
```bash
python manage.py test --verbosity=2
```

### Run Tests in Parallel (faster)
```bash
python manage.py test --parallel
```

## Test Coverage

### Install Coverage Tool
```bash
pip install coverage
```

### Run Tests with Coverage
```bash
coverage run --source='household' manage.py test
coverage report
coverage html
```

### View HTML Coverage Report
After running `coverage html`, open `htmlcov/index.html` in your browser.

## Test Structure

```
household/
├── tests/
│   ├── __init__.py
│   ├── test_models.py      # Tests for models
│   ├── test_views.py        # Tests for views
│   ├── test_utils.py        # Tests for utility functions
│   ├── test_forms.py        # Tests for forms (if any)
│   └── factories.py         # Factory classes for test data
```

## Writing Tests

### Model Tests Example

```python
from django.test import TestCase
from household.models import Room

class RoomModelTest(TestCase):
    def setUp(self):
        """Set up test data before each test."""
        self.room = Room.objects.create(
            name="Living Room",
            room_type="living_room",
            floor=1
        )
    
    def test_room_creation(self):
        """Test that room can be created."""
        self.assertEqual(self.room.name, "Living Room")
    
    def test_room_str(self):
        """Test room string representation."""
        self.assertEqual(str(self.room), "Living Room (Living Room)")
```

### View Tests Example

```python
from django.test import TestCase, Client
from django.urls import reverse

class RoomViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.room = Room.objects.create(name="Kitchen", room_type="kitchen")
    
    def test_room_list_view(self):
        """Test room list page loads."""
        response = self.client.get(reverse('room_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Kitchen")
```

### Utility Function Tests Example

```python
from django.test import TestCase
from unittest.mock import patch
from household.utils import search_manual_online

class SearchManualTest(TestCase):
    def test_search_with_mock(self):
        """Test search function with mocked HTTP request."""
        with patch('household.utils.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_get.return_value = mock_response
            
            result = search_manual_online("Samsung", "RF28R7351SG", "Refrigerator")
            mock_get.assert_called()
```

## Using Factories

Factories make it easy to create test data:

```python
from household.tests.factories import RoomFactory, ApplianceFactory

def test_something(self):
    room = RoomFactory(name="Custom Room")
    appliance = ApplianceFactory(room=room, brand="Samsung")
    # Use room and appliance in your test
```

## Test Best Practices

1. **Use setUp()** - Set up common test data in setUp method
2. **Test Names** - Use descriptive test method names starting with `test_`
3. **One Assertion** - Ideally one assertion per test (but multiple related assertions are OK)
4. **Isolation** - Each test should be independent
5. **Mock External Services** - Mock HTTP requests, file operations, etc.
6. **Test Edge Cases** - Test empty inputs, None values, boundary conditions
7. **Test Both Success and Failure** - Test both happy path and error cases

## Common Test Patterns

### Testing Model Methods
```python
def test_model_method(self):
    room = Room.objects.create(name="Test Room")
    url = room.get_absolute_url()
    self.assertIn(str(room.pk), url)
```

### Testing Forms
```python
def test_form_validation(self):
    form = RoomForm(data={'name': ''})  # Empty name
    self.assertFalse(form.is_valid())
    self.assertIn('name', form.errors)
```

### Testing Views with Authentication
```python
def setUp(self):
    self.user = User.objects.create_user('testuser', 'test@example.com', 'password')
    self.client.login(username='testuser', password='password')
```

### Testing Redirects
```python
def test_redirect_after_create(self):
    response = self.client.post(reverse('room_create'), {'name': 'New Room'})
    self.assertRedirects(response, reverse('room_list'))
```

### Testing Messages
```python
from django.contrib.messages import get_messages

def test_success_message(self):
    response = self.client.post(reverse('room_create'), {'name': 'New Room'})
    messages = list(get_messages(response.wsgi_request))
    self.assertEqual(str(messages[0]), 'Room created successfully!')
```

## Continuous Integration

### GitHub Actions Example

Create `.github/workflows/tests.yml`:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.11
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      - name: Run tests
        run: |
          python manage.py test
      - name: Generate coverage
        run: |
          coverage run --source='household' manage.py test
          coverage report
```

## Troubleshooting

### Tests Not Finding Modules
Make sure you're in the project root directory and Django is properly configured.

### Database Issues
Tests use a separate test database. If you have issues, try:
```bash
python manage.py test --keepdb  # Reuse test database
```

### Slow Tests
- Use `--parallel` to run tests in parallel
- Use factories instead of creating objects manually
- Mock external API calls and file operations

### Test Data Persistence
Tests run in transactions that are rolled back. Data doesn't persist between tests.

## Current Test Coverage

- ✅ Model creation and validation
- ✅ Model methods (__str__, get_absolute_url, calculate_next_due)
- ✅ View rendering and status codes
- ✅ Form submission and redirects
- ✅ Utility functions with mocks
- ✅ Maintenance task scheduling logic

## Adding New Tests

When adding new features:

1. **Add model tests** in `test_models.py`
2. **Add view tests** in `test_views.py`
3. **Add utility tests** in `test_utils.py`
4. **Update factories** in `factories.py` if needed
5. **Run tests** to ensure they pass
6. **Check coverage** to ensure new code is tested

## Running Tests in CI/CD

For automated testing in CI/CD pipelines:

```bash
# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Run tests
python manage.py test --verbosity=2

# Generate coverage report
coverage run --source='household' manage.py test
coverage report
coverage xml  # For CI tools
```

