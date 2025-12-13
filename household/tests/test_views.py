"""
Tests for household views.
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from household.models import Room, Appliance, Vendor, Invoice, MaintenanceTask
from datetime import date


class HomeViewTest(TestCase):
    """Test cases for home view."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        Room.objects.create(name="Living Room", room_type="living_room")
        Appliance.objects.create(name="Refrigerator", appliance_type="refrigerator")
        Vendor.objects.create(name="ABC Plumbing", service_type="plumbing")
    
    def test_home_view(self):
        """Test home page loads successfully."""
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Household Manager")
    
    def test_home_view_context(self):
        """Test home view context data."""
        response = self.client.get(reverse('home'))
        self.assertIn('room_count', response.context)
        self.assertIn('appliance_count', response.context)
        self.assertIn('vendor_count', response.context)


class RoomViewTest(TestCase):
    """Test cases for room views."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.room = Room.objects.create(
            name="Kitchen",
            room_type="kitchen",
            floor=1
        )
    
    def test_room_list_view(self):
        """Test room list view."""
        response = self.client.get(reverse('room_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Kitchen")
    
    def test_room_detail_view(self):
        """Test room detail view."""
        response = self.client.get(reverse('room_detail', args=[self.room.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.room.name)
    
    def test_room_create_view(self):
        """Test room creation."""
        response = self.client.post(reverse('room_create'), {
            'name': 'Bedroom',
            'room_type': 'bedroom',
            'floor': 2,
            'square_feet': 200.00
        })
        self.assertEqual(response.status_code, 302)  # Redirect after creation
        self.assertTrue(Room.objects.filter(name='Bedroom').exists())
    
    def test_room_update_view(self):
        """Test room update."""
        response = self.client.post(
            reverse('room_update', args=[self.room.pk]),
            {
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
        self.room = Room.objects.create(name="Kitchen", room_type="kitchen")
        self.appliance = Appliance.objects.create(
            name="Refrigerator",
            brand="Samsung",
            model_number="RF28R7351SG",
            appliance_type="refrigerator",
            room=self.room
        )
    
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
            'name': 'Dishwasher',
            'brand': 'Whirlpool',
            'appliance_type': 'dishwasher',
            'room': self.room.pk
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Appliance.objects.filter(name='Dishwasher').exists())
    
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
        self.appliance = Appliance.objects.create(
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
        self.vendor = Vendor.objects.create(
            name="ABC Plumbing",
            email="contact@abcplumbing.com",
            service_type="plumbing"
        )
    
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
        self.vendor = Vendor.objects.create(name="ABC Plumbing", service_type="plumbing")
        self.invoice = Invoice.objects.create(
            invoice_number="INV-001",
            vendor=self.vendor,
            invoice_date=date.today(),
            amount=500.00,
            tax_amount=50.00,
            total_amount=550.00
        )
    
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

