"""
Tests for household views.
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import PermissionDenied
from PIL import Image
from io import BytesIO
from household.models import House, Room, Appliance, Vendor, Invoice, MaintenanceTask
from datetime import date


class HomeViewTest(TestCase):
    """Test cases for home view."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.user = User.objects.create_user('testuser', 'test@example.com', 'password')
        self.house = House.objects.create(address="123 Test Street")
        self.house.owners.add(self.user)
        self.room = Room.objects.create(house=self.house, name="Living Room", room_type="living_room")
        self.appliance = Appliance.objects.create(house=self.house, name="Refrigerator", appliance_type="refrigerator")
        self.vendor = Vendor.objects.create(house=self.house, name="ABC Plumbing", service_type="plumbing")
    
    def test_home_view_requires_login(self):
        """Test home page requires login."""
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
        self.assertIn('/accounts/login', response.url)
    
    def test_home_view(self):
        """Test home page loads successfully for logged in user."""
        self.client.login(username='testuser', password='password')
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Household Manager")
    
    def test_home_view_context(self):
        """Test home view context data."""
        self.client.login(username='testuser', password='password')
        response = self.client.get(reverse('home'))
        self.assertIn('room_count', response.context)
        self.assertIn('appliance_count', response.context)
        self.assertIn('vendor_count', response.context)
        self.assertIn('user_houses', response.context)


class RoomViewTest(TestCase):
    """Test cases for room views."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.user = User.objects.create_user('testuser', 'test@example.com', 'password')
        self.other_user = User.objects.create_user('otheruser', 'other@example.com', 'password')
        self.house = House.objects.create(address="123 Test Street")
        self.house.owners.add(self.user)
        self.room = Room.objects.create(
            house=self.house,
            name="Kitchen",
            room_type="kitchen",
            floor=1
        )
        self.client.login(username='testuser', password='password')
    
    def test_room_list_view_requires_login(self):
        """Test room list requires login."""
        self.client.logout()
        response = self.client.get(reverse('room_list'))
        self.assertEqual(response.status_code, 302)
    
    def test_room_list_view(self):
        """Test room list view."""
        response = self.client.get(reverse('room_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Kitchen")
    
    def test_room_list_view_filters_by_house(self):
        """Test room list only shows user's houses."""
        other_house = House.objects.create(address="456 Other Street")
        other_house.owners.add(self.other_user)
        Room.objects.create(house=other_house, name="Other Room", room_type="bedroom")
        
        response = self.client.get(reverse('room_list'))
        self.assertContains(response, "Kitchen")
        self.assertNotContains(response, "Other Room")
    
    def test_room_detail_view(self):
        """Test room detail view."""
        response = self.client.get(reverse('room_detail', args=[self.room.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.room.name)
    
    def test_room_detail_view_permission_denied(self):
        """Test room detail blocks access to other houses."""
        other_house = House.objects.create(address="456 Other Street")
        other_house.owners.add(self.other_user)
        other_room = Room.objects.create(house=other_house, name="Other Room")
        
        response = self.client.get(reverse('room_detail', args=[other_room.pk]))
        self.assertEqual(response.status_code, 403)  # Permission denied
    
    def test_room_create_view(self):
        """Test room creation."""
        response = self.client.post(reverse('room_create'), {
            'house': self.house.pk,
            'name': 'Bedroom',
            'room_type': 'bedroom',
            'floor': 2,
            'square_feet': 200.00
        })
        self.assertEqual(response.status_code, 302)  # Redirect after creation
        self.assertTrue(Room.objects.filter(name='Bedroom', house=self.house).exists())
    
    def test_room_update_view(self):
        """Test room update."""
        response = self.client.post(
            reverse('room_update', args=[self.room.pk]),
            {
                'house': self.house.pk,
                'name': 'Updated Kitchen',
                'room_type': 'kitchen',
                'floor': 1
            }
        )
        self.assertEqual(response.status_code, 302)
        self.room.refresh_from_db()
        self.assertEqual(self.room.name, 'Updated Kitchen')
    
    def test_room_delete_view(self):
        """Test room deletion."""
        room_id = self.room.pk
        response = self.client.post(reverse('room_delete', args=[room_id]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Room.objects.filter(pk=room_id).exists())


class ApplianceViewTest(TestCase):
    """Test cases for appliance views."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.user = User.objects.create_user('testuser', 'test@example.com', 'password')
        self.house = House.objects.create(address="123 Test Street")
        self.house.owners.add(self.user)
        self.room = Room.objects.create(house=self.house, name="Kitchen", room_type="kitchen")
        self.appliance = Appliance.objects.create(
            house=self.house,
            name="Refrigerator",
            brand="Samsung",
            model_number="RF28R7351SG",
            appliance_type="refrigerator",
            room=self.room
        )
        self.client.login(username='testuser', password='password')
    
    def test_appliance_list_view(self):
        """Test appliance list view."""
        response = self.client.get(reverse('appliance_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Refrigerator")
    
    def test_appliance_detail_view(self):
        """Test appliance detail view."""
        response = self.client.get(reverse('appliance_detail', args=[self.appliance.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.appliance.name)
    
    def test_appliance_create_view(self):
        """Test appliance creation."""
        response = self.client.post(reverse('appliance_create'), {
            'house': self.house.pk,
            'name': 'Dishwasher',
            'brand': 'Whirlpool',
            'appliance_type': 'dishwasher',
            'room': self.room.pk
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Appliance.objects.filter(name='Dishwasher', house=self.house).exists())
    
    def test_search_manual_view(self):
        """Test search manual functionality."""
        response = self.client.post(reverse('search_manual', args=[self.appliance.pk]))
        # Should redirect back to appliance detail
        self.assertEqual(response.status_code, 302)


class MaintenanceTaskViewTest(TestCase):
    """Test cases for maintenance task views."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.user = User.objects.create_user('testuser', 'test@example.com', 'password')
        self.house = House.objects.create(address="123 Test Street")
        self.house.owners.add(self.user)
        self.appliance = Appliance.objects.create(
            house=self.house,
            name="Refrigerator",
            appliance_type="refrigerator"
        )
        self.task = MaintenanceTask.objects.create(
            appliance=self.appliance,
            task_name="Clean Filter",
            description="Clean the air filter",
            frequency="monthly",
            last_performed=date(2024, 1, 1)
        )
        self.client.login(username='testuser', password='password')
    
    def test_maintenance_task_list_view(self):
        """Test maintenance task list view."""
        response = self.client.get(reverse('maintenance_task_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Clean Filter")
    
    def test_maintenance_task_detail_view(self):
        """Test maintenance task detail view."""
        response = self.client.get(reverse('maintenance_task_detail', args=[self.task.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.task.task_name)
    
    def test_maintenance_task_create_view(self):
        """Test maintenance task creation."""
        response = self.client.post(reverse('maintenance_task_create'), {
            'appliance': self.appliance.pk,
            'task_name': 'Inspect Coils',
            'description': 'Inspect condenser coils',
            'frequency': 'quarterly',
            'estimated_duration': 60,
            'difficulty': 'medium'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(MaintenanceTask.objects.filter(task_name='Inspect Coils').exists())
    
    def test_mark_maintenance_complete(self):
        """Test marking maintenance task as complete."""
        old_last_performed = self.task.last_performed
        response = self.client.post(reverse('mark_maintenance_complete', args=[self.task.pk]))
        self.assertEqual(response.status_code, 302)
        self.task.refresh_from_db()
        self.assertEqual(self.task.last_performed, date.today())
        self.assertIsNotNone(self.task.next_due)


class VendorViewTest(TestCase):
    """Test cases for vendor views."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.user = User.objects.create_user('testuser', 'test@example.com', 'password')
        self.house = House.objects.create(address="123 Test Street")
        self.house.owners.add(self.user)
        self.vendor = Vendor.objects.create(
            house=self.house,
            name="ABC Plumbing",
            email="contact@abcplumbing.com",
            service_type="plumbing"
        )
        self.client.login(username='testuser', password='password')
    
    def test_vendor_list_view(self):
        """Test vendor list view."""
        response = self.client.get(reverse('vendor_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "ABC Plumbing")
    
    def test_vendor_detail_view(self):
        """Test vendor detail view."""
        response = self.client.get(reverse('vendor_detail', args=[self.vendor.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.vendor.name)


class InvoiceViewTest(TestCase):
    """Test cases for invoice views."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.user = User.objects.create_user('testuser', 'test@example.com', 'password')
        self.house = House.objects.create(address="123 Test Street")
        self.house.owners.add(self.user)
        self.vendor = Vendor.objects.create(house=self.house, name="ABC Plumbing", service_type="plumbing")
        self.invoice = Invoice.objects.create(
            house=self.house,
            invoice_number="INV-001",
            vendor=self.vendor,
            invoice_date=date.today(),
            amount=500.00,
            tax_amount=50.00,
            total_amount=550.00
        )
        self.client.login(username='testuser', password='password')
    
    def test_invoice_list_view(self):
        """Test invoice list view."""
        response = self.client.get(reverse('invoice_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "INV-001")
    
    def test_invoice_detail_view(self):
        """Test invoice detail view."""
        response = self.client.get(reverse('invoice_detail', args=[self.invoice.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.invoice.invoice_number)


class ExtractLabelInfoViewTest(TestCase):
    """Test cases for extract_label_info view."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.user = User.objects.create_user('testuser', 'test@example.com', 'password')
        self.client.login(username='testuser', password='password')
    
    def create_test_image(self):
        """Create a test image file."""
        image = Image.new('RGB', (100, 100), color='white')
        image_file = BytesIO()
        image.save(image_file, format='PNG')
        image_file.seek(0)
        return SimpleUploadedFile(
            "test_label.png",
            image_file.read(),
            content_type="image/png"
        )
    
    def test_extract_label_info_success(self):
        """Test successful label info extraction."""
        from unittest.mock import patch
        
        image_file = self.create_test_image()
        
        with patch('household.views.extract_appliance_info_from_image') as mock_extract:
            mock_extract.return_value = {
                'success': True,
                'extracted_text': 'SAMSUNG MODEL RF28R7351SG SERIAL SN123456',
                'brand': 'Samsung',
                'model_number': 'RF28R7351SG',
                'serial_number': 'SN123456'
            }
            
            response = self.client.post(
                reverse('extract_label_info'),
                {'label_image': image_file},
                format='multipart'
            )
            
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertTrue(data['success'])
            self.assertEqual(data['brand'], 'Samsung')
            self.assertEqual(data['model_number'], 'RF28R7351SG')
            self.assertEqual(data['serial_number'], 'SN123456')
    
    def test_extract_label_info_no_file(self):
        """Test extraction without image file."""
        response = self.client.post(reverse('extract_label_info'))
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertIn('error', data)
    
    def test_extract_label_info_invalid_file(self):
        """Test extraction with non-image file."""
        invalid_file = SimpleUploadedFile(
            "test.txt",
            b"not an image",
            content_type="text/plain"
        )
        
        response = self.client.post(
            reverse('extract_label_info'),
            {'label_image': invalid_file},
            format='multipart'
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertIn('error', data)
    
    def test_extract_label_info_extraction_error(self):
        """Test handling of extraction errors."""
        from unittest.mock import patch
        
        image_file = self.create_test_image()
        
        with patch('household.views.extract_appliance_info_from_image') as mock_extract:
            mock_extract.side_effect = Exception("OCR processing error")
            
            response = self.client.post(
                reverse('extract_label_info'),
                {'label_image': image_file},
                format='multipart'
            )
            
            self.assertEqual(response.status_code, 500)
            data = response.json()
            self.assertFalse(data['success'])
            self.assertIn('error', data)
    
    def test_extract_label_info_no_text_found(self):
        """Test extraction when no text is found in image."""
        from unittest.mock import patch
        
        image_file = self.create_test_image()
        
        with patch('household.views.extract_appliance_info_from_image') as mock_extract:
            mock_extract.return_value = {
                'success': False,
                'error': 'Could not extract text from image',
                'extracted_text': '',
                'brand': None,
                'model_number': None,
                'serial_number': None
            }
            
            response = self.client.post(
                reverse('extract_label_info'),
                {'label_image': image_file},
                format='multipart'
            )
            
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertFalse(data['success'])
            self.assertIn('error', data)

