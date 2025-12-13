from django.contrib import admin
from .models import Room, Appliance, Vendor, Invoice


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ['name', 'room_type', 'floor', 'square_feet', 'created_at']
    list_filter = ['room_type', 'floor']
    search_fields = ['name', 'description']
    ordering = ['floor', 'name']


@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ['name', 'contact_person', 'email', 'phone', 'service_type', 'created_at']
    list_filter = ['service_type']
    search_fields = ['name', 'contact_person', 'email', 'phone']
    ordering = ['name']


@admin.register(Appliance)
class ApplianceAdmin(admin.ModelAdmin):
    list_display = ['name', 'brand', 'appliance_type', 'room', 'purchase_date', 'warranty_expiry']
    list_filter = ['appliance_type', 'room', 'purchase_date']
    search_fields = ['name', 'brand', 'model_number', 'serial_number']
    ordering = ['room', 'name']
    date_hierarchy = 'purchase_date'


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['invoice_number', 'vendor', 'invoice_date', 'total_amount', 'paid', 'category']
    list_filter = ['paid', 'category', 'invoice_date', 'vendor']
    search_fields = ['invoice_number', 'vendor__name', 'description']
    ordering = ['-invoice_date']
    date_hierarchy = 'invoice_date'
    readonly_fields = ['created_at', 'updated_at']



