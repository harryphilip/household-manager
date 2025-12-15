"""
Forms for household app.
"""
from django import forms
from django.forms import inlineformset_factory
from .models import Invoice, InvoiceLineItem, Room, Appliance, MaintenanceTask


class InvoiceForm(forms.ModelForm):
    """Form for Invoice with date pickers."""
    
    class Meta:
        model = Invoice
        fields = ['house', 'invoice_number', 'vendor', 'invoice_date', 'due_date', 'amount', 
                  'tax_amount', 'total_amount', 'category', 'description', 'paid', 
                  'paid_date', 'payment_method', 'invoice_file', 'related_appliance', 'notes']
        widgets = {
            'invoice_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'due_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'paid_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'house': forms.Select(attrs={'class': 'form-control'}),
            'invoice_number': forms.TextInput(attrs={'class': 'form-control'}),
            'vendor': forms.Select(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'tax_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'total_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'paid': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'payment_method': forms.Select(attrs={'class': 'form-control'}),
            'invoice_file': forms.FileInput(attrs={'class': 'form-control'}),
            'related_appliance': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make house field required
        self.fields['house'].required = True
        # Make amount field not required if line items will be used
        # It will be calculated from line items if they exist
        self.fields['amount'].required = False
        self.fields['amount'].help_text = "Subtotal (will be calculated from line items if provided)"


class ApplianceForm(forms.ModelForm):
    """Form for Appliance with date pickers."""
    
    class Meta:
        model = Appliance
        fields = ['house', 'name', 'brand', 'model_number', 'serial_number', 'appliance_type',
                  'room', 'purchase_date', 'warranty_expiry', 'purchase_price', 
                  'label_image', 'manual_pdf', 'notes']
        widgets = {
            'purchase_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'warranty_expiry': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'house': forms.Select(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'brand': forms.TextInput(attrs={'class': 'form-control'}),
            'model_number': forms.TextInput(attrs={'class': 'form-control'}),
            'serial_number': forms.TextInput(attrs={'class': 'form-control'}),
            'appliance_type': forms.Select(attrs={'class': 'form-control'}),
            'room': forms.Select(attrs={'class': 'form-control'}),
            'purchase_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'label_image': forms.FileInput(attrs={'class': 'form-control'}),
            'manual_pdf': forms.FileInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class MaintenanceTaskForm(forms.ModelForm):
    """Form for MaintenanceTask with date pickers."""
    
    class Meta:
        model = MaintenanceTask
        fields = ['appliance', 'task_name', 'description', 'frequency', 'interval_days',
                  'last_performed', 'next_due', 'estimated_duration', 'difficulty',
                  'parts_needed', 'instructions', 'is_active']
        widgets = {
            'last_performed': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'next_due': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'appliance': forms.Select(attrs={'class': 'form-control'}),
            'task_name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'frequency': forms.Select(attrs={'class': 'form-control'}),
            'interval_days': forms.NumberInput(attrs={'class': 'form-control'}),
            'estimated_duration': forms.NumberInput(attrs={'class': 'form-control'}),
            'difficulty': forms.Select(attrs={'class': 'form-control'}),
            'parts_needed': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'instructions': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class InvoiceLineItemForm(forms.ModelForm):
    """Form for invoice line items."""
    
    class Meta:
        model = InvoiceLineItem
        fields = ['description', 'quantity', 'unit_price', 'line_total', 'rooms', 'appliances']
        widgets = {
            'description': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Item description'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'line_total': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'readonly': True}),
            'rooms': forms.SelectMultiple(attrs={'class': 'form-control'}),
            'appliances': forms.SelectMultiple(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter rooms and appliances based on invoice's house
        invoice = None
        if self.instance and self.instance.pk and self.instance.invoice:
            invoice = self.instance.invoice
        elif 'invoice' in kwargs.get('initial', {}):
            invoice = kwargs['initial'].get('invoice')
        elif hasattr(self, 'invoice'):
            invoice = self.invoice
        
        if invoice and invoice.house:
            self.fields['rooms'].queryset = invoice.house.rooms.all()
            self.fields['appliances'].queryset = invoice.house.appliances.all()
        else:
            # Default to empty queryset if no house context
            self.fields['rooms'].queryset = Room.objects.none()
            self.fields['appliances'].queryset = Appliance.objects.none()


# Create formset factory for invoice line items
InvoiceLineItemFormSet = inlineformset_factory(
    Invoice,
    InvoiceLineItem,
    form=InvoiceLineItemForm,
    extra=1,
    can_delete=True,
    min_num=0,
    validate_min=False,
)

