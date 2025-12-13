"""
Tests for household models.
"""
from django.test import TestCase
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import date, timedelta
from household.models import House, Room, Appliance, Vendor, Invoice, InvoiceLineItem, MaintenanceTask


class HouseModelTest(TestCase):
    """Test cases for House model."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user('testuser', 'test@example.com', 'password')
        self.house = House.objects.create(
            address="123 Test Street",
            city="Test City",
            state="TS",
            zip_code="12345"
        )
        self.house.owners.add(self.user)
    
    def test_house_creation(self):
        """Test house can be created."""
        self.assertEqual(self.house.address, "123 Test Street")
        self.assertEqual(self.house.city, "Test City")
        self.assertTrue(self.house.can_user_view(self.user))
        self.assertTrue(self.house.can_user_edit(self.user))
        self.assertTrue(self.house.can_user_delete(self.user))
    
    def test_house_permissions(self):
        """Test house permission methods."""
        admin_user = User.objects.create_user('admin', 'admin@example.com', 'password')
        viewer_user = User.objects.create_user('viewer', 'viewer@example.com', 'password')
        other_user = User.objects.create_user('other', 'other@example.com', 'password')
        
        self.house.admins.add(admin_user)
        self.house.viewers.add(viewer_user)
        
        # Owner permissions
        self.assertTrue(self.house.can_user_view(self.user))
        self.assertTrue(self.house.can_user_edit(self.user))
        self.assertTrue(self.house.can_user_delete(self.user))
        
        # Admin permissions
        self.assertTrue(self.house.can_user_view(admin_user))
        self.assertTrue(self.house.can_user_edit(admin_user))
        self.assertFalse(self.house.can_user_delete(admin_user))
        
        # Viewer permissions
        self.assertTrue(self.house.can_user_view(viewer_user))
        self.assertFalse(self.house.can_user_edit(viewer_user))
        self.assertFalse(self.house.can_user_delete(viewer_user))
        
        # Other user permissions
        self.assertFalse(self.house.can_user_view(other_user))
        self.assertFalse(self.house.can_user_edit(other_user))
        self.assertFalse(self.house.can_user_delete(other_user))


class RoomModelTest(TestCase):
    """Test cases for Room model."""
    
    def setUp(self):
        """Set up test data."""
        self.house = House.objects.create(address="123 Test Street")
        self.room = Room.objects.create(
            house=self.house,
            name="Living Room",
            room_type="living_room",
            floor=1,
            square_feet=300.50
        )
    
    def test_room_creation(self):
        """Test room can be created."""
        self.assertEqual(self.room.name, "Living Room")
        self.assertEqual(self.room.room_type, "living_room")
        self.assertEqual(self.room.floor, 1)
        self.assertEqual(float(self.room.square_feet), 300.50)
    
    def test_room_str(self):
        """Test room string representation."""
        self.assertEqual(str(self.room), "Living Room (Living Room)")
    
    def test_room_get_absolute_url(self):
        """Test room absolute URL."""
        url = self.room.get_absolute_url()
        self.assertEqual(url, f'/rooms/{self.room.pk}/')


class ApplianceModelTest(TestCase):
    """Test cases for Appliance model."""
    
    def setUp(self):
        """Set up test data."""
        self.house = House.objects.create(address="123 Test Street")
        self.room = Room.objects.create(
            house=self.house,
            name="Kitchen",
            room_type="kitchen",
            floor=1
        )
        self.appliance = Appliance.objects.create(
            house=self.house,
            name="Refrigerator",
            brand="Samsung",
            model_number="RF28R7351SG",
            serial_number="SN123456",
            appliance_type="refrigerator",
            room=self.room,
            purchase_date=date(2020, 1, 15),
            warranty_expiry=date(2025, 1, 15),
            purchase_price=1500.00
        )
    
    def test_appliance_creation(self):
        """Test appliance can be created."""
        self.assertEqual(self.appliance.name, "Refrigerator")
        self.assertEqual(self.appliance.brand, "Samsung")
        self.assertEqual(self.appliance.model_number, "RF28R7351SG")
        self.assertEqual(self.appliance.room, self.room)
    
    def test_appliance_str(self):
        """Test appliance string representation."""
        self.assertEqual(str(self.appliance), "Refrigerator (Kitchen)")
    
    def test_appliance_without_room(self):
        """Test appliance without room assignment."""
        appliance = Appliance.objects.create(
            house=self.house,
            name="Portable Heater",
            appliance_type="heater"
        )
        self.assertIsNone(appliance.room)
        self.assertEqual(str(appliance), "Portable Heater (No Room)")


class VendorModelTest(TestCase):
    """Test cases for Vendor model."""
    
    def setUp(self):
        """Set up test data."""
        self.house = House.objects.create(address="123 Test Street")
        self.vendor = Vendor.objects.create(
            house=self.house,
            name="ABC Plumbing",
            contact_person="John Doe",
            email="john@abcplumbing.com",
            phone="555-1234",
            service_type="plumbing"
        )
    
    def test_vendor_creation(self):
        """Test vendor can be created."""
        self.assertEqual(self.vendor.name, "ABC Plumbing")
        self.assertEqual(self.vendor.contact_person, "John Doe")
        self.assertEqual(self.vendor.service_type, "plumbing")
    
    def test_vendor_str(self):
        """Test vendor string representation."""
        self.assertEqual(str(self.vendor), "ABC Plumbing")


class InvoiceModelTest(TestCase):
    """Test cases for Invoice model."""
    
    def setUp(self):
        """Set up test data."""
        self.house = House.objects.create(address="123 Test Street")
        self.vendor = Vendor.objects.create(
            house=self.house,
            name="ABC Plumbing",
            service_type="plumbing"
        )
        self.appliance = Appliance.objects.create(
            house=self.house,
            name="Water Heater",
            appliance_type="water_heater"
        )
        self.invoice = Invoice.objects.create(
            house=self.house,
            invoice_number="INV-001",
            vendor=self.vendor,
            invoice_date=date(2024, 1, 15),
            due_date=date(2024, 2, 15),
            amount=500.00,
            tax_amount=50.00,
            total_amount=550.00,
            category="maintenance",
            related_appliance=self.appliance
        )
    
    def test_invoice_creation(self):
        """Test invoice can be created."""
        self.assertEqual(self.invoice.invoice_number, "INV-001")
        self.assertEqual(self.invoice.vendor, self.vendor)
        self.assertEqual(float(self.invoice.total_amount), 550.00)
    
    def test_invoice_str(self):
        """Test invoice string representation."""
        expected = f"Invoice #INV-001 - {self.vendor.name}"
        self.assertEqual(str(self.invoice), expected)
    
    def test_invoice_total_calculation(self):
        """Test invoice total is calculated automatically."""
        invoice = Invoice.objects.create(
            house=self.house,
            invoice_number="INV-002",
            vendor=self.vendor,
            invoice_date=date.today(),
            amount=100.00,
            tax_amount=10.00
        )
        # Total should be calculated automatically
        self.assertEqual(float(invoice.total_amount), 110.00)
    
    def test_invoice_without_vendor(self):
        """Test invoice without vendor."""
        invoice = Invoice.objects.create(
            house=self.house,
            invoice_number="INV-003",
            invoice_date=date.today(),
            amount=200.00,
            tax_amount=20.00,
            total_amount=220.00
        )
        self.assertIsNone(invoice.vendor)
        self.assertEqual(str(invoice), "Invoice #INV-003 - Unknown Vendor")
    
    def test_invoice_calculate_from_line_items(self):
        """Test invoice amount calculation from line items."""
        invoice = Invoice.objects.create(
            house=self.house,
            invoice_number="INV-004",
            vendor=self.vendor,
            invoice_date=date.today(),
            amount=0,  # Will be calculated
            tax_amount=10.00
        )
        # Invoice must be saved before creating line items
        
        # Create line items
        line_item1 = InvoiceLineItem.objects.create(
            invoice=invoice,
            description="Item 1",
            quantity=2,
            unit_price=50.00,
            line_total=100.00
        )
        line_item2 = InvoiceLineItem.objects.create(
            invoice=invoice,
            description="Item 2",
            quantity=1,
            unit_price=75.00,
            line_total=75.00
        )
        
        # Refresh invoice from database
        invoice.refresh_from_db()
        
        # Calculate amounts
        calculated_amount = invoice.calculate_amount_from_line_items()
        self.assertEqual(float(calculated_amount), 175.00)
        
        calculated_total = invoice.calculate_total()
        self.assertEqual(float(calculated_total), 185.00)  # 175 + 10 tax
        
        # Save should update amounts
        invoice.save()
        invoice.refresh_from_db()
        self.assertEqual(float(invoice.amount), 175.00)
        self.assertEqual(float(invoice.total_amount), 185.00)


class InvoiceLineItemModelTest(TestCase):
    """Test cases for InvoiceLineItem model."""
    
    def setUp(self):
        """Set up test data."""
        self.house = House.objects.create(address="123 Test Street")
        self.vendor = Vendor.objects.create(
            house=self.house,
            name="ABC Plumbing",
            service_type="plumbing"
        )
        self.invoice = Invoice.objects.create(
            house=self.house,
            invoice_number="INV-001",
            vendor=self.vendor,
            invoice_date=date.today(),
            amount=100.00,
            tax_amount=10.00,
            total_amount=110.00
        )
        self.room = Room.objects.create(
            house=self.house,
            name="Kitchen",
            room_type="kitchen"
        )
        self.appliance = Appliance.objects.create(
            house=self.house,
            name="Refrigerator",
            appliance_type="refrigerator"
        )
    
    def test_line_item_creation(self):
        """Test line item can be created."""
        line_item = InvoiceLineItem.objects.create(
            invoice=self.invoice,
            description="Service Call",
            quantity=1,
            unit_price=100.00,
            line_total=100.00
        )
        self.assertEqual(line_item.description, "Service Call")
        self.assertEqual(float(line_item.line_total), 100.00)
    
    def test_line_item_auto_calculate_total(self):
        """Test line total is calculated automatically."""
        line_item = InvoiceLineItem.objects.create(
            invoice=self.invoice,
            description="Item",
            quantity=3,
            unit_price=25.00
            # line_total not provided
        )
        self.assertEqual(float(line_item.line_total), 75.00)
    
    def test_line_item_with_rooms_and_appliances(self):
        """Test line item with rooms and appliances."""
        line_item = InvoiceLineItem.objects.create(
            invoice=self.invoice,
            description="Kitchen Repair",
            quantity=1,
            unit_price=150.00,
            line_total=150.00
        )
        line_item.rooms.add(self.room)
        line_item.appliances.add(self.appliance)
        
        self.assertEqual(line_item.rooms.count(), 1)
        self.assertIn(self.room, line_item.rooms.all())
        self.assertEqual(line_item.appliances.count(), 1)
        self.assertIn(self.appliance, line_item.appliances.all())
    
    def test_line_item_str(self):
        """Test line item string representation."""
        line_item = InvoiceLineItem.objects.create(
            invoice=self.invoice,
            description="Test Item",
            quantity=1,
            unit_price=50.00,
            line_total=50.00
        )
        expected = f"{self.invoice.invoice_number} - Test Item"
        self.assertEqual(str(line_item), expected)


class MaintenanceTaskModelTest(TestCase):
    """Test cases for MaintenanceTask model."""
    
    def setUp(self):
        """Set up test data."""
        self.house = House.objects.create(address="123 Test Street")
        self.appliance = Appliance.objects.create(
            house=self.house,
            name="Refrigerator",
            brand="Samsung",
            appliance_type="refrigerator"
        )
        self.task = MaintenanceTask.objects.create(
            appliance=self.appliance,
            task_name="Clean Filter",
            description="Clean the air filter",
            frequency="monthly",
            last_performed=date(2024, 1, 1),
            estimated_duration=30,
            difficulty="easy"
        )
    
    def test_maintenance_task_creation(self):
        """Test maintenance task can be created."""
        self.assertEqual(self.task.task_name, "Clean Filter")
        self.assertEqual(self.task.appliance, self.appliance)
        self.assertEqual(self.task.frequency, "monthly")
    
    def test_maintenance_task_str(self):
        """Test maintenance task string representation."""
        expected = f"{self.appliance.name} - {self.task.task_name}"
        self.assertEqual(str(self.task), expected)
    
    def test_calculate_next_due_daily(self):
        """Test next due date calculation for daily frequency."""
        task = MaintenanceTask.objects.create(
            appliance=self.appliance,
            task_name="Daily Check",
            frequency="daily",
            last_performed=date(2024, 1, 1)
        )
        next_due = task.calculate_next_due()
        self.assertEqual(next_due, date(2024, 1, 2))
    
    def test_calculate_next_due_weekly(self):
        """Test next due date calculation for weekly frequency."""
        task = MaintenanceTask.objects.create(
            appliance=self.appliance,
            task_name="Weekly Check",
            frequency="weekly",
            last_performed=date(2024, 1, 1)
        )
        next_due = task.calculate_next_due()
        self.assertEqual(next_due, date(2024, 1, 8))
    
    def test_calculate_next_due_monthly(self):
        """Test next due date calculation for monthly frequency."""
        task = MaintenanceTask.objects.create(
            appliance=self.appliance,
            task_name="Monthly Check",
            frequency="monthly",
            last_performed=date(2024, 1, 15)
        )
        next_due = task.calculate_next_due()
        # Should be approximately one month later
        self.assertIsNotNone(next_due)
        self.assertGreater(next_due, date(2024, 1, 15))
    
    def test_calculate_next_due_custom(self):
        """Test next due date calculation for custom frequency."""
        task = MaintenanceTask.objects.create(
            appliance=self.appliance,
            task_name="Custom Check",
            frequency="custom",
            interval_days=45,
            last_performed=date(2024, 1, 1)
        )
        next_due = task.calculate_next_due()
        self.assertEqual(next_due, date(2024, 2, 15))
    
    def test_auto_calculate_next_due_on_save(self):
        """Test next due is calculated automatically on save."""
        task = MaintenanceTask.objects.create(
            appliance=self.appliance,
            task_name="Auto Calculate Test",
            frequency="weekly",
            last_performed=date(2024, 1, 1)
        )
        # Next due should be calculated automatically
        self.assertIsNotNone(task.next_due)
        self.assertEqual(task.next_due, date(2024, 1, 8))

