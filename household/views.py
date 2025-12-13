from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from datetime import date
import json
from .models import Room, Appliance, Vendor, Invoice, MaintenanceTask
from .utils import (
    search_manual_online, download_pdf, extract_text_from_pdf,
    extract_maintenance_info, extract_maintenance_with_ai,
    extract_appliance_info_from_image
)


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
              'room', 'purchase_date', 'warranty_expiry', 'purchase_price', 
              'label_image', 'manual_pdf', 'notes']
    success_url = reverse_lazy('appliance_list')

    def form_valid(self, form):
        messages.success(self.request, 'Appliance created successfully!')
        return super().form_valid(form)


class ApplianceUpdateView(UpdateView):
    model = Appliance
    template_name = 'household/appliance_form.html'
    fields = ['name', 'brand', 'model_number', 'serial_number', 'appliance_type', 
              'room', 'purchase_date', 'warranty_expiry', 'purchase_price', 
              'label_image', 'manual_pdf', 'notes']
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


# Manual Search and Maintenance Views

@require_http_methods(["POST"])
def search_manual(request, pk):
    """Search for appliance manual online."""
    appliance = get_object_or_404(Appliance, pk=pk)
    
    if not appliance.brand and not appliance.model_number:
        messages.error(request, 'Brand or Model Number is required to search for manual.')
        return redirect('appliance_detail', pk=pk)
    
    try:
        result = search_manual_online(appliance.brand, appliance.model_number, appliance.name)
        if result:
            appliance.manual_url = result['url']
            appliance.save()
            messages.success(request, f'Manual found! URL saved. You can download it now.')
        else:
            messages.warning(request, 'No manual found online. Try uploading manually.')
    except Exception as e:
        messages.error(request, f'Error searching for manual: {str(e)}')
    
    return redirect('appliance_detail', pk=pk)


@require_http_methods(["POST"])
def download_manual(request, pk):
    """Download manual from URL and save to appliance."""
    appliance = get_object_or_404(Appliance, pk=pk)
    
    if not appliance.manual_url:
        messages.error(request, 'No manual URL found. Please search for a manual first.')
        return redirect('appliance_detail', pk=pk)
    
    try:
        pdf_file = download_pdf(appliance.manual_url, appliance.name)
        if pdf_file:
            appliance.manual_pdf.save(pdf_file.name, pdf_file, save=True)
            messages.success(request, 'Manual downloaded and saved successfully!')
        else:
            messages.error(request, 'Failed to download PDF. Please check the URL.')
    except Exception as e:
        messages.error(request, f'Error downloading manual: {str(e)}')
    
    return redirect('appliance_detail', pk=pk)


@require_http_methods(["POST"])
def extract_maintenance(request, pk):
    """Extract maintenance tasks from uploaded manual PDF."""
    appliance = get_object_or_404(Appliance, pk=pk)
    
    if not appliance.manual_pdf:
        messages.error(request, 'No manual PDF found. Please upload or download a manual first.')
        return redirect('appliance_detail', pk=pk)
    
    try:
        # Extract text from PDF
        pdf_file = appliance.manual_pdf.open('rb')
        text = extract_text_from_pdf(pdf_file)
        pdf_file.close()
        
        if not text or len(text) < 100:
            messages.warning(request, 'Could not extract enough text from PDF. The PDF might be scanned or corrupted.')
            return redirect('appliance_detail', pk=pk)
        
        # Extract maintenance tasks
        tasks = extract_maintenance_with_ai(text, appliance.appliance_type)
        
        if not tasks:
            messages.warning(request, 'No maintenance tasks found in the manual.')
            return redirect('appliance_detail', pk=pk)
        
        # Create maintenance task objects
        created_count = 0
        for task_data in tasks:
            task, created = MaintenanceTask.objects.get_or_create(
                appliance=appliance,
                task_name=task_data['task_name'],
                defaults={
                    'description': task_data.get('description', ''),
                    'frequency': task_data.get('frequency', 'monthly'),
                    'extracted_from_manual': True,
                    'is_active': True,
                }
            )
            if created:
                created_count += 1
        
        messages.success(request, f'Extracted {created_count} maintenance task(s) from the manual!')
    except Exception as e:
        messages.error(request, f'Error extracting maintenance: {str(e)}')
    
    return redirect('appliance_detail', pk=pk)


# Maintenance Task Views

class MaintenanceTaskListView(ListView):
    model = MaintenanceTask
    template_name = 'household/maintenance_task_list.html'
    context_object_name = 'tasks'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = MaintenanceTask.objects.filter(is_active=True)
        appliance_id = self.request.GET.get('appliance')
        if appliance_id:
            queryset = queryset.filter(appliance_id=appliance_id)
        return queryset.order_by('next_due', 'appliance')


class MaintenanceTaskDetailView(DetailView):
    model = MaintenanceTask
    template_name = 'household/maintenance_task_detail.html'
    context_object_name = 'task'


class MaintenanceTaskCreateView(CreateView):
    model = MaintenanceTask
    template_name = 'household/maintenance_task_form.html'
    fields = ['appliance', 'task_name', 'description', 'frequency', 'interval_days',
              'last_performed', 'estimated_duration', 'difficulty', 'parts_needed', 'instructions']
    
    def get_success_url(self):
        return reverse_lazy('appliance_detail', kwargs={'pk': self.object.appliance.pk})
    
    def form_valid(self, form):
        messages.success(self.request, 'Maintenance task created successfully!')
        return super().form_valid(form)


class MaintenanceTaskUpdateView(UpdateView):
    model = MaintenanceTask
    template_name = 'household/maintenance_task_form.html'
    fields = ['appliance', 'task_name', 'description', 'frequency', 'interval_days',
              'last_performed', 'next_due', 'estimated_duration', 'difficulty', 
              'parts_needed', 'instructions', 'is_active']
    
    def get_success_url(self):
        return reverse_lazy('appliance_detail', kwargs={'pk': self.object.appliance.pk})
    
    def form_valid(self, form):
        # Recalculate next_due if last_performed changed
        if 'last_performed' in form.changed_data:
            task = form.save(commit=False)
            if task.last_performed:
                task.next_due = task.calculate_next_due()
            task.save()
        messages.success(self.request, 'Maintenance task updated successfully!')
        return super().form_valid(form)


class MaintenanceTaskDeleteView(DeleteView):
    model = MaintenanceTask
    template_name = 'household/maintenance_task_confirm_delete.html'
    
    def get_success_url(self):
        return reverse_lazy('appliance_detail', kwargs={'pk': self.object.appliance.pk})
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Maintenance task deleted successfully!')
        return super().delete(request, *args, **kwargs)


@require_http_methods(["POST"])
def mark_maintenance_complete(request, pk):
    """Mark a maintenance task as complete and update next due date."""
    task = get_object_or_404(MaintenanceTask, pk=pk)
    task.last_performed = date.today()
    task.next_due = task.calculate_next_due()
    task.save()
    messages.success(request, f'Maintenance task "{task.task_name}" marked as complete!')
    return redirect('appliance_detail', pk=task.appliance.pk)


@require_http_methods(["POST"])
def extract_info_from_label(request):
    """Extract appliance information from uploaded label image."""
    if 'label_image' not in request.FILES:
        return JsonResponse({
            'success': False,
            'error': 'No image file provided'
        }, status=400)
    
    image_file = request.FILES['label_image']
    
    # Validate file type
    if not image_file.content_type.startswith('image/'):
        return JsonResponse({
            'success': False,
            'error': 'File must be an image'
        }, status=400)
    
    try:
        # Extract information from image
        result = extract_appliance_info_from_image(image_file)
        
        return JsonResponse(result)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error processing image: {str(e)}',
            'extracted_text': '',
            'brand': None,
            'model_number': None,
            'serial_number': None,
        }, status=500)



