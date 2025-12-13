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
    manual_pdf = models.FileField(upload_to='manuals/', blank=True, null=True, help_text="User manual PDF")
    manual_url = models.URLField(blank=True, help_text="URL to the manual if found online")
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


class MaintenanceTask(models.Model):
    """Model representing a maintenance task for an appliance."""
    FREQUENCY_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly (Every 3 months)'),
        ('semi_annual', 'Semi-Annual (Every 6 months)'),
        ('annual', 'Annual (Yearly)'),
        ('as_needed', 'As Needed'),
        ('custom', 'Custom Interval'),
    ]
    
    appliance = models.ForeignKey(Appliance, on_delete=models.CASCADE, related_name='maintenance_tasks')
    task_name = models.CharField(max_length=200)
    description = models.TextField(help_text="Detailed description of the maintenance task")
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, default='monthly')
    interval_days = models.IntegerField(null=True, blank=True, help_text="Custom interval in days (if frequency is 'custom')")
    last_performed = models.DateField(null=True, blank=True)
    next_due = models.DateField(null=True, blank=True)
    estimated_duration = models.IntegerField(null=True, blank=True, help_text="Estimated duration in minutes")
    difficulty = models.CharField(
        max_length=20,
        choices=[
            ('easy', 'Easy'),
            ('medium', 'Medium'),
            ('hard', 'Hard'),
            ('professional', 'Requires Professional'),
        ],
        default='medium'
    )
    parts_needed = models.TextField(blank=True, help_text="List of parts or supplies needed")
    instructions = models.TextField(blank=True, help_text="Step-by-step instructions")
    extracted_from_manual = models.BooleanField(default=False, help_text="Whether this was extracted from the manual")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['appliance', 'next_due', 'task_name']
        indexes = [
            models.Index(fields=['appliance', 'next_due']),
        ]

    def __str__(self):
        return f"{self.appliance.name} - {self.task_name}"

    def get_absolute_url(self):
        return reverse('maintenance_task_detail', kwargs={'pk': self.pk})

    def calculate_next_due(self):
        """Calculate the next due date based on frequency and last performed date."""
        from datetime import date, timedelta
        try:
            from dateutil.relativedelta import relativedelta
        except ImportError:
            # Fallback if dateutil is not available
            relativedelta = None
        
        if not self.last_performed:
            return None
        
        last = self.last_performed
        if isinstance(last, str):
            from datetime import datetime
            last = datetime.strptime(last, '%Y-%m-%d').date()
        
        if self.frequency == 'daily':
            next_due = last + timedelta(days=1)
        elif self.frequency == 'weekly':
            next_due = last + timedelta(weeks=1)
        elif self.frequency == 'monthly':
            if relativedelta:
                next_due = last + relativedelta(months=1)
            else:
                next_due = last + timedelta(days=30)
        elif self.frequency == 'quarterly':
            if relativedelta:
                next_due = last + relativedelta(months=3)
            else:
                next_due = last + timedelta(days=90)
        elif self.frequency == 'semi_annual':
            if relativedelta:
                next_due = last + relativedelta(months=6)
            else:
                next_due = last + timedelta(days=180)
        elif self.frequency == 'annual':
            if relativedelta:
                next_due = last + relativedelta(years=1)
            else:
                next_due = last + timedelta(days=365)
        elif self.frequency == 'custom' and self.interval_days:
            next_due = last + timedelta(days=self.interval_days)
        else:
            return None
        
        return next_due

    def save(self, *args, **kwargs):
        if self.last_performed and not self.next_due:
            self.next_due = self.calculate_next_due()
        super().save(*args, **kwargs)


