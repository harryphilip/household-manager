from django.contrib import admin
from .models import House, Room, Appliance, Vendor, Invoice, MaintenanceTask


@admin.register(House)
class HouseAdmin(admin.ModelAdmin):
    list_display = ['address', 'city', 'state', 'zip_code', 'created_at']
    list_filter = ['country', 'state', 'city']
    search_fields = ['address', 'city', 'state', 'zip_code']
    filter_horizontal = ['owners', 'admins', 'viewers']
    ordering = ['address']


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ['name', 'house', 'room_type', 'floor', 'square_feet', 'created_at']
    list_filter = ['room_type', 'floor', 'house']
    search_fields = ['name', 'description', 'house__address']
    ordering = ['house', 'floor', 'name']


@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ['name', 'house', 'contact_person', 'email', 'phone', 'service_type', 'created_at']
    list_filter = ['service_type', 'house']
    search_fields = ['name', 'contact_person', 'email', 'phone', 'house__address']
    ordering = ['house', 'name']


@admin.register(Appliance)
class ApplianceAdmin(admin.ModelAdmin):
    list_display = ['name', 'house', 'brand', 'appliance_type', 'room', 'purchase_date', 'warranty_expiry']
    list_filter = ['appliance_type', 'room', 'purchase_date', 'house']
    search_fields = ['name', 'brand', 'model_number', 'serial_number', 'house__address']
    ordering = ['house', 'room', 'name']
    date_hierarchy = 'purchase_date'


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['invoice_number', 'house', 'vendor', 'invoice_date', 'total_amount', 'paid', 'category']
    list_filter = ['paid', 'category', 'invoice_date', 'vendor', 'house']
    search_fields = ['invoice_number', 'vendor__name', 'description', 'house__address']
    ordering = ['-invoice_date']
    date_hierarchy = 'invoice_date'
    readonly_fields = ['created_at', 'updated_at']


@admin.register(MaintenanceTask)
class MaintenanceTaskAdmin(admin.ModelAdmin):
    list_display = ['task_name', 'appliance', 'frequency', 'last_performed', 'next_due', 'is_active']
    list_filter = ['frequency', 'difficulty', 'is_active', 'extracted_from_manual']
    search_fields = ['task_name', 'description', 'appliance__name']
    ordering = ['appliance', 'next_due']
    date_hierarchy = 'next_due'
    readonly_fields = ['created_at', 'updated_at']



