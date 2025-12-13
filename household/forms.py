"""
Forms for household app.
"""
from django import forms
from django.forms import inlineformset_factory
from .models import Invoice, InvoiceLineItem, Room, Appliance


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

