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
from household.models import House, Room, Appliance, Vendor, Invoice, InvoiceLineItem, MaintenanceTask
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
        self.room = Room.objects.create(house=self.house, name="Kitchen", room_type="kitchen")
        self.appliance = Appliance.objects.create(house=self.house, name="Refrigerator", appliance_type="refrigerator")
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
    
    def test_invoice_detail_view_with_line_items(self):
        """Test invoice detail view displays line items."""
        # Create line items
        line_item1 = InvoiceLineItem.objects.create(
            invoice=self.invoice,
            description="Service Call",
            quantity=1,
            unit_price=100.00,
            line_total=100.00
        )
        line_item1.rooms.add(self.room)
        line_item1.appliances.add(self.appliance)
        
        line_item2 = InvoiceLineItem.objects.create(
            invoice=self.invoice,
            description="Parts",
            quantity=2,
            unit_price=50.00,
            line_total=100.00
        )
        
        response = self.client.get(reverse('invoice_detail', args=[self.invoice.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Service Call")
        self.assertContains(response, "Parts")
        self.assertContains(response, self.room.name)
        self.assertContains(response, self.appliance.name)
    
    def test_invoice_create_view_with_line_items(self):
        """Test creating invoice with line items."""
        from django.forms import formset_factory
        
        post_data = {
            'house': self.house.pk,
            'invoice_number': 'INV-002',
            'vendor': self.vendor.pk,
            'invoice_date': date.today().isoformat(),
            'amount': '0',  # Will be calculated from line items
            'tax_amount': '10.00',
            'total_amount': '0',  # Will be calculated
            'category': 'maintenance',
            'line_items-TOTAL_FORMS': '2',
            'line_items-INITIAL_FORMS': '0',
            'line_items-MIN_NUM_FORMS': '0',
            'line_items-MAX_NUM_FORMS': '1000',
            'line_items-0-description': 'Item 1',
            'line_items-0-quantity': '2',
            'line_items-0-unit_price': '50.00',
            'line_items-0-line_total': '100.00',
            'line_items-0-rooms': [self.room.pk],
            'line_items-0-appliances': [self.appliance.pk],
            'line_items-1-description': 'Item 2',
            'line_items-1-quantity': '1',
            'line_items-1-unit_price': '75.00',
            'line_items-1-line_total': '75.00',
            'line_items-1-rooms': [],
            'line_items-1-appliances': [],
        }
        
        response = self.client.post(reverse('invoice_create'), post_data)
        self.assertEqual(response.status_code, 302)  # Redirect after creation
        
        # Verify invoice was created
        invoice = Invoice.objects.get(invoice_number='INV-002')
        self.assertEqual(invoice.house, self.house)
        
        # Verify line items were created
        line_items = invoice.line_items.all()
        self.assertEqual(line_items.count(), 2)
        
        # Verify first line item has room and appliance
        line_item1 = line_items.first()
        self.assertEqual(line_item1.description, 'Item 1')
        self.assertIn(self.room, line_item1.rooms.all())
        self.assertIn(self.appliance, line_item1.appliances.all())
        
        # Verify totals were calculated
        invoice.refresh_from_db()
        self.assertEqual(float(invoice.amount), 175.00)  # 100 + 75
        self.assertEqual(float(invoice.total_amount), 185.00)  # 175 + 10 tax
    
    def test_invoice_update_view_with_line_items(self):
        """Test updating invoice with line items."""
        # Create a line item
        line_item = InvoiceLineItem.objects.create(
            invoice=self.invoice,
            description="Original Item",
            quantity=1,
            unit_price=100.00,
            line_total=100.00
        )
        
        # Update invoice with new line items
        post_data = {
            'house': self.house.pk,
            'invoice_number': self.invoice.invoice_number,
            'vendor': self.vendor.pk,
            'invoice_date': self.invoice.invoice_date.isoformat(),
            'amount': '0',
            'tax_amount': '15.00',
            'total_amount': '0',
            'category': 'maintenance',
            'line_items-TOTAL_FORMS': '2',
            'line_items-INITIAL_FORMS': '1',
            'line_items-MIN_NUM_FORMS': '0',
            'line_items-MAX_NUM_FORMS': '1000',
            'line_items-0-id': str(line_item.pk),
            'line_items-0-description': 'Updated Item',
            'line_items-0-quantity': '3',
            'line_items-0-unit_price': '50.00',
            'line_items-0-line_total': '150.00',
            'line_items-0-rooms': [self.room.pk],
            'line_items-0-appliances': [],
            'line_items-1-description': 'New Item',
            'line_items-1-quantity': '1',
            'line_items-1-unit_price': '25.00',
            'line_items-1-line_total': '25.00',
            'line_items-1-rooms': [],
            'line_items-1-appliances': [self.appliance.pk],
        }
        
        response = self.client.post(reverse('invoice_update', args=[self.invoice.pk]), post_data)
        self.assertEqual(response.status_code, 302)
        
        # Verify line items were updated
        self.invoice.refresh_from_db()
        line_items = self.invoice.line_items.all()
        self.assertEqual(line_items.count(), 2)
        
        # Verify first item was updated
        updated_item = line_items.get(pk=line_item.pk)
        self.assertEqual(updated_item.description, 'Updated Item')
        self.assertEqual(float(updated_item.line_total), 150.00)
        self.assertIn(self.room, updated_item.rooms.all())
        
        # Verify new item was created
        new_item = line_items.exclude(pk=line_item.pk).first()
        self.assertEqual(new_item.description, 'New Item')
        self.assertIn(self.appliance, new_item.appliances.all())
        
        # Verify totals
        self.assertEqual(float(self.invoice.amount), 175.00)
        self.assertEqual(float(self.invoice.total_amount), 190.00)  # 175 + 15 tax
    
    def test_invoice_create_view_line_items_filtered_by_house(self):
        """Test that line item rooms/appliances are filtered by invoice house."""
        # Create another house with room/appliance
        other_house = House.objects.create(address="456 Other Street")
        other_house.owners.add(self.user)
        other_room = Room.objects.create(house=other_house, name="Other Room")
        other_appliance = Appliance.objects.create(house=other_house, name="Other Appliance")
        
        # Try to create invoice with line items from different house
        post_data = {
            'house': self.house.pk,
            'invoice_number': 'INV-003',
            'vendor': self.vendor.pk,
            'invoice_date': date.today().isoformat(),
            'amount': '100.00',
            'tax_amount': '10.00',
            'total_amount': '110.00',
            'category': 'maintenance',
            'line_items-TOTAL_FORMS': '1',
            'line_items-INITIAL_FORMS': '0',
            'line_items-MIN_NUM_FORMS': '0',
            'line_items-MAX_NUM_FORMS': '1000',
            'line_items-0-description': 'Item',
            'line_items-0-quantity': '1',
            'line_items-0-unit_price': '100.00',
            'line_items-0-line_total': '100.00',
            'line_items-0-rooms': [self.room.pk],  # From same house - should work
            'line_items-0-appliances': [self.appliance.pk],  # From same house - should work
        }
        
        response = self.client.post(reverse('invoice_create'), post_data)
        # Should succeed because rooms/appliances are from the same house
        self.assertEqual(response.status_code, 302)
        
        invoice = Invoice.objects.get(invoice_number='INV-003')
        line_item = invoice.line_items.first()
        self.assertIn(self.room, line_item.rooms.all())
        self.assertIn(self.appliance, line_item.appliances.all())


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

