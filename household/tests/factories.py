"""
Factory classes for creating test data easily.
Uses factory-boy for generating test fixtures.
"""
import factory
from django.utils import timezone
from datetime import date, timedelta
from household.models import Room, Appliance, Vendor, Invoice, MaintenanceTask


class RoomFactory(factory.django.DjangoModelFactory):
    """Factory for creating Room test instances."""
    
    class Meta:
        model = Room
    
    name = factory.Sequence(lambda n: f"Room {n}")
    room_type = "living_room"
    floor = 1
    square_feet = factory.Faker('pyfloat', left_digits=3, right_digits=2, positive=True)


class ApplianceFactory(factory.django.DjangoModelFactory):
    """Factory for creating Appliance test instances."""
    
    class Meta:
        model = Appliance
    
    name = factory.Sequence(lambda n: f"Appliance {n}")
    brand = factory.Faker('company')
    model_number = factory.Faker('bothify', text='MOD-####')
    serial_number = factory.Faker('bothify', text='SN-########')
    appliance_type = "refrigerator"
    room = factory.SubFactory(RoomFactory)
    purchase_date = factory.Faker('date_between', start_date='-5y', end_date='today')
    purchase_price = factory.Faker('pyfloat', left_digits=4, right_digits=2, positive=True)


class VendorFactory(factory.django.DjangoModelFactory):
    """Factory for creating Vendor test instances."""
    
    class Meta:
        model = Vendor
    
    name = factory.Sequence(lambda n: f"Vendor {n}")
    contact_person = factory.Faker('name')
    email = factory.Faker('email')
    phone = factory.Faker('phone_number')
    service_type = "plumbing"


class InvoiceFactory(factory.django.DjangoModelFactory):
    """Factory for creating Invoice test instances."""
    
    class Meta:
        model = Invoice
    
    invoice_number = factory.Sequence(lambda n: f"INV-{n:04d}")
    vendor = factory.SubFactory(VendorFactory)
    invoice_date = factory.Faker('date_between', start_date='-1y', end_date='today')
    amount = factory.Faker('pyfloat', left_digits=3, right_digits=2, positive=True)
    tax_amount = factory.LazyAttribute(lambda obj: obj.amount * 0.1)
    total_amount = factory.LazyAttribute(lambda obj: obj.amount + obj.tax_amount)
    category = "maintenance"
    paid = factory.Faker('boolean')


class MaintenanceTaskFactory(factory.django.DjangoModelFactory):
    """Factory for creating MaintenanceTask test instances."""
    
    class Meta:
        model = MaintenanceTask
    
    appliance = factory.SubFactory(ApplianceFactory)
    task_name = factory.Sequence(lambda n: f"Task {n}")
    description = factory.Faker('text', max_nb_chars=200)
    frequency = "monthly"
    last_performed = factory.Faker('date_between', start_date='-1y', end_date='today')
    estimated_duration = factory.Faker('random_int', min=15, max=120)
    difficulty = "medium"
    is_active = True

