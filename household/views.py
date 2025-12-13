from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from .models import Room, Appliance, Vendor, Invoice


def home(request):
    """Home page with dashboard statistics."""
    context = {
        'room_count': Room.objects.count(),
        'appliance_count': Appliance.objects.count(),
        'vendor_count': Vendor.objects.count(),
        'invoice_count': Invoice.objects.count(),
        'total_invoice_amount': sum(inv.total_amount for inv in Invoice.objects.all()),
        'recent_rooms': Room.objects.all()[:5],
        'recent_appliances': Appliance.objects.all()[:5],
        'recent_invoices': Invoice.objects.all()[:5],
    }
    return render(request, 'household/home.html', context)


class RoomListView(ListView):
    model = Room
    template_name = 'household/room_list.html'
    context_object_name = 'rooms'
    paginate_by = 20


class RoomDetailView(DetailView):
    model = Room
    template_name = 'household/room_detail.html'
    context_object_name = 'room'


class RoomCreateView(CreateView):
    model = Room
    template_name = 'household/room_form.html'
    fields = ['name', 'room_type', 'floor', 'square_feet', 'description']
    success_url = reverse_lazy('room_list')

    def form_valid(self, form):
        messages.success(self.request, 'Room created successfully!')
        return super().form_valid(form)


class RoomUpdateView(UpdateView):
    model = Room
    template_name = 'household/room_form.html'
    fields = ['name', 'room_type', 'floor', 'square_feet', 'description']
    success_url = reverse_lazy('room_list')

    def form_valid(self, form):
        messages.success(self.request, 'Room updated successfully!')
        return super().form_valid(form)


class RoomDeleteView(DeleteView):
    model = Room
    template_name = 'household/room_confirm_delete.html'
    success_url = reverse_lazy('room_list')

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Room deleted successfully!')
        return super().delete(request, *args, **kwargs)


class ApplianceListView(ListView):
    model = Appliance
    template_name = 'household/appliance_list.html'
    context_object_name = 'appliances'
    paginate_by = 20


class ApplianceDetailView(DetailView):
    model = Appliance
    template_name = 'household/appliance_detail.html'
    context_object_name = 'appliance'


class ApplianceCreateView(CreateView):
    model = Appliance
    template_name = 'household/appliance_form.html'
    fields = ['name', 'brand', 'model_number', 'serial_number', 'appliance_type', 
              'room', 'purchase_date', 'warranty_expiry', 'purchase_price', 'notes']
    success_url = reverse_lazy('appliance_list')

    def form_valid(self, form):
        messages.success(self.request, 'Appliance created successfully!')
        return super().form_valid(form)


class ApplianceUpdateView(UpdateView):
    model = Appliance
    template_name = 'household/appliance_form.html'
    fields = ['name', 'brand', 'model_number', 'serial_number', 'appliance_type', 
              'room', 'purchase_date', 'warranty_expiry', 'purchase_price', 'notes']
    success_url = reverse_lazy('appliance_list')

    def form_valid(self, form):
        messages.success(self.request, 'Appliance updated successfully!')
        return super().form_valid(form)


class ApplianceDeleteView(DeleteView):
    model = Appliance
    template_name = 'household/appliance_confirm_delete.html'
    success_url = reverse_lazy('appliance_list')

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Appliance deleted successfully!')
        return super().delete(request, *args, **kwargs)


class VendorListView(ListView):
    model = Vendor
    template_name = 'household/vendor_list.html'
    context_object_name = 'vendors'
    paginate_by = 20


class VendorDetailView(DetailView):
    model = Vendor
    template_name = 'household/vendor_detail.html'
    context_object_name = 'vendor'


class VendorCreateView(CreateView):
    model = Vendor
    template_name = 'household/vendor_form.html'
    fields = ['name', 'contact_person', 'email', 'phone', 'address', 
              'website', 'service_type', 'notes']
    success_url = reverse_lazy('vendor_list')

    def form_valid(self, form):
        messages.success(self.request, 'Vendor created successfully!')
        return super().form_valid(form)


class VendorUpdateView(UpdateView):
    model = Vendor
    template_name = 'household/vendor_form.html'
    fields = ['name', 'contact_person', 'email', 'phone', 'address', 
              'website', 'service_type', 'notes']
    success_url = reverse_lazy('vendor_list')

    def form_valid(self, form):
        messages.success(self.request, 'Vendor updated successfully!')
        return super().form_valid(form)


class VendorDeleteView(DeleteView):
    model = Vendor
    template_name = 'household/vendor_confirm_delete.html'
    success_url = reverse_lazy('vendor_list')

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Vendor deleted successfully!')
        return super().delete(request, *args, **kwargs)


class InvoiceListView(ListView):
    model = Invoice
    template_name = 'household/invoice_list.html'
    context_object_name = 'invoices'
    paginate_by = 20


class InvoiceDetailView(DetailView):
    model = Invoice
    template_name = 'household/invoice_detail.html'
    context_object_name = 'invoice'


class InvoiceCreateView(CreateView):
    model = Invoice
    template_name = 'household/invoice_form.html'
    fields = ['invoice_number', 'vendor', 'invoice_date', 'due_date', 'amount', 
              'tax_amount', 'total_amount', 'category', 'description', 'paid', 
              'paid_date', 'payment_method', 'invoice_file', 'related_appliance', 'notes']
    success_url = reverse_lazy('invoice_list')

    def form_valid(self, form):
        messages.success(self.request, 'Invoice created successfully!')
        return super().form_valid(form)


class InvoiceUpdateView(UpdateView):
    model = Invoice
    template_name = 'household/invoice_form.html'
    fields = ['invoice_number', 'vendor', 'invoice_date', 'due_date', 'amount', 
              'tax_amount', 'total_amount', 'category', 'description', 'paid', 
              'paid_date', 'payment_method', 'invoice_file', 'related_appliance', 'notes']
    success_url = reverse_lazy('invoice_list')

    def form_valid(self, form):
        messages.success(self.request, 'Invoice updated successfully!')
        return super().form_valid(form)


class InvoiceDeleteView(DeleteView):
    model = Invoice
    template_name = 'household/invoice_confirm_delete.html'
    success_url = reverse_lazy('invoice_list')

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Invoice deleted successfully!')
        return super().delete(request, *args, **kwargs)



