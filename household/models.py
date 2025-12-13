from django.db import models
from django.urls import reverse


class Room(models.Model):
    """Model representing a room in the household."""
    name = models.CharField(max_length=100)
    room_type = models.CharField(
        max_length=50,
        choices=[
            ('bedroom', 'Bedroom'),
            ('bathroom', 'Bathroom'),
            ('kitchen', 'Kitchen'),
            ('living_room', 'Living Room'),
            ('dining_room', 'Dining Room'),
            ('office', 'Office'),
            ('basement', 'Basement'),
            ('attic', 'Attic'),
            ('garage', 'Garage'),
            ('other', 'Other'),
        ],
        default='other'
    )
    floor = models.IntegerField(default=1, help_text="Floor number (1 for ground floor)")
    square_feet = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['floor', 'name']

    def __str__(self):
        return f"{self.name} ({self.get_room_type_display()})"

    def get_absolute_url(self):
        return reverse('room_detail', kwargs={'pk': self.pk})


class Vendor(models.Model):
    """Model representing a vendor/service provider."""
    name = models.CharField(max_length=200)
    contact_person = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    website = models.URLField(blank=True)
    service_type = models.CharField(
        max_length=50,
        choices=[
            ('plumbing', 'Plumbing'),
            ('electrical', 'Electrical'),
            ('hvac', 'HVAC'),
            ('appliance_repair', 'Appliance Repair'),
            ('cleaning', 'Cleaning'),
            ('landscaping', 'Landscaping'),
            ('general_contractor', 'General Contractor'),
            ('other', 'Other'),
        ],
        default='other'
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('vendor_detail', kwargs={'pk': self.pk})


class Appliance(models.Model):
    """Model representing an appliance in the household."""
    name = models.CharField(max_length=200)
    brand = models.CharField(max_length=100, blank=True)
    model_number = models.CharField(max_length=100, blank=True)
    serial_number = models.CharField(max_length=100, blank=True)
    appliance_type = models.CharField(
        max_length=50,
        choices=[
            ('refrigerator', 'Refrigerator'),
            ('oven', 'Oven'),
            ('dishwasher', 'Dishwasher'),
            ('washer', 'Washer'),
            ('dryer', 'Dryer'),
            ('microwave', 'Microwave'),
            ('air_conditioner', 'Air Conditioner'),
            ('heater', 'Heater'),
            ('water_heater', 'Water Heater'),
            ('furnace', 'Furnace'),
            ('other', 'Other'),
        ],
        default='other'
    )
    room = models.ForeignKey(Room, on_delete=models.SET_NULL, null=True, blank=True, related_name='appliances')
    purchase_date = models.DateField(null=True, blank=True)
    warranty_expiry = models.DateField(null=True, blank=True)
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['room', 'name']

    def __str__(self):
        room_name = self.room.name if self.room else "No Room"
        return f"{self.name} ({room_name})"

    def get_absolute_url(self):
        return reverse('appliance_detail', kwargs={'pk': self.pk})


class Invoice(models.Model):
    """Model representing a past invoice/bill."""
    invoice_number = models.CharField(max_length=100, unique=True)
    vendor = models.ForeignKey(Vendor, on_delete=models.SET_NULL, null=True, blank=True, related_name='invoices')
    invoice_date = models.DateField()
    due_date = models.DateField(null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(
        max_length=50,
        choices=[
            ('appliance_repair', 'Appliance Repair'),
            ('maintenance', 'Maintenance'),
            ('utility', 'Utility'),
            ('renovation', 'Renovation'),
            ('purchase', 'Purchase'),
            ('service', 'Service'),
            ('other', 'Other'),
        ],
        default='other'
    )
    description = models.TextField(blank=True)
    paid = models.BooleanField(default=False)
    paid_date = models.DateField(null=True, blank=True)
    payment_method = models.CharField(
        max_length=50,
        choices=[
            ('cash', 'Cash'),
            ('check', 'Check'),
            ('credit_card', 'Credit Card'),
            ('debit_card', 'Debit Card'),
            ('bank_transfer', 'Bank Transfer'),
            ('other', 'Other'),
        ],
        blank=True
    )
    invoice_file = models.FileField(upload_to='invoices/', blank=True, null=True)
    related_appliance = models.ForeignKey(Appliance, on_delete=models.SET_NULL, null=True, blank=True, related_name='invoices')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-invoice_date', '-created_at']

    def __str__(self):
        return f"Invoice #{self.invoice_number} - {self.vendor.name if self.vendor else 'Unknown Vendor'}"

    def get_absolute_url(self):
        return reverse('invoice_detail', kwargs={'pk': self.pk})

    def save(self, *args, **kwargs):
        if not self.total_amount:
            self.total_amount = self.amount + self.tax_amount
        super().save(*args, **kwargs)



