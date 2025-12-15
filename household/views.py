from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from datetime import date
import json
from .models import House, Room, Appliance, Vendor, Invoice, InvoiceLineItem, MaintenanceTask
from .forms import InvoiceLineItemFormSet, InvoiceForm, ApplianceForm, MaintenanceTaskForm
from .permissions import (
    get_user_houses, get_user_editable_houses, require_house_access,
    filter_by_user_house
)
from .utils import (
    search_manual_online, download_pdf, extract_text_from_pdf,
    extract_maintenance_info, extract_maintenance_with_ai,
    extract_appliance_info_from_image
)


@login_required
def home(request):
    """Home page with dashboard statistics for user's houses."""
    # Get user's houses
    user_houses = get_user_houses(request.user)
    
    # Get statistics for all user's houses
    rooms = filter_by_user_house(Room.objects.all(), request.user)
    appliances = filter_by_user_house(Appliance.objects.all(), request.user)
    vendors = filter_by_user_house(Vendor.objects.all(), request.user)
    invoices = filter_by_user_house(Invoice.objects.all(), request.user)
    
    context = {
        'user_houses': user_houses,
        'room_count': rooms.count(),
        'appliance_count': appliances.count(),
        'vendor_count': vendors.count(),
        'invoice_count': invoices.count(),
        'total_invoice_amount': sum(inv.total_amount for inv in invoices),
        'recent_rooms': rooms[:5],
        'recent_appliances': appliances[:5],
        'recent_invoices': invoices[:5],
    }
    return render(request, 'household/home.html', context)


# House Management Views
class HouseListView(LoginRequiredMixin, ListView):
    """List all houses the user has access to."""
    model = House
    template_name = 'household/house_list.html'
    context_object_name = 'houses'
    
    def get_queryset(self):
        return get_user_houses(self.request.user)


class HouseDetailView(LoginRequiredMixin, DetailView):
    """View house details."""
    model = House
    template_name = 'household/house_detail.html'
    context_object_name = 'house'
    
    def get_object(self, queryset=None):
        house = super().get_object(queryset)
        require_house_access(self.request.user, house)
        return house


class HouseCreateView(LoginRequiredMixin, CreateView):
    """Create a new house."""
    model = House
    template_name = 'household/house_form.html'
    fields = ['address', 'city', 'state', 'zip_code', 'country']
    
    def form_valid(self, form):
        house = form.save()
        # Add current user as owner
        house.owners.add(self.request.user)
        messages.success(self.request, 'House created successfully!')
        return super().form_valid(form)


class HouseUpdateView(LoginRequiredMixin, UpdateView):
    """Update house details."""
    model = House
    template_name = 'household/house_form.html'
    fields = ['address', 'city', 'state', 'zip_code', 'country', 'owners', 'admins', 'viewers']
    
    def get_object(self, queryset=None):
        house = super().get_object(queryset)
        require_house_access(self.request.user, house, require_edit=True)
        return house


class HouseDeleteView(LoginRequiredMixin, DeleteView):
    """Delete a house."""
    model = House
    template_name = 'household/house_confirm_delete.html'
    success_url = reverse_lazy('house_list')
    
    def get_object(self, queryset=None):
        house = super().get_object(queryset)
        require_house_access(self.request.user, house, require_edit=True)
        # Only owners can delete
        if not house.can_user_delete(self.request.user):
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied("Only owners can delete a house.")
        return house


# Room Views
class RoomListView(LoginRequiredMixin, ListView):
    model = Room
    template_name = 'household/room_list.html'
    context_object_name = 'rooms'
    
    def get_queryset(self):
        queryset = Room.objects.all()
        # Filter by house if specified
        house_id = self.request.GET.get('house')
        return filter_by_user_house(queryset, self.request.user, house_id)
    paginate_by = 20


class RoomDetailView(LoginRequiredMixin, DetailView):
    model = Room
    template_name = 'household/room_detail.html'
    context_object_name = 'room'
    
    def get_object(self, queryset=None):
        room = super().get_object(queryset)
        require_house_access(self.request.user, room.house)
        return room


class RoomCreateView(LoginRequiredMixin, CreateView):
    model = Room
    template_name = 'household/room_form.html'
    fields = ['house', 'name', 'room_type', 'floor', 'square_feet', 'description']
    success_url = reverse_lazy('room_list')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Only show houses user can edit
        form.fields['house'].queryset = get_user_editable_houses(self.request.user)
        return form

    def form_valid(self, form):
        # Verify user can edit the selected house
        require_house_access(self.request.user, form.cleaned_data['house'], require_edit=True)
        messages.success(self.request, 'Room created successfully!')
        return super().form_valid(form)


class RoomUpdateView(LoginRequiredMixin, UpdateView):
    model = Room
    template_name = 'household/room_form.html'
    fields = ['house', 'name', 'room_type', 'floor', 'square_feet', 'description']
    success_url = reverse_lazy('room_list')

    def get_object(self, queryset=None):
        room = super().get_object(queryset)
        require_house_access(self.request.user, room.house, require_edit=True)
        return room

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['house'].queryset = get_user_editable_houses(self.request.user)
        return form

    def form_valid(self, form):
        require_house_access(self.request.user, form.cleaned_data['house'], require_edit=True)
        messages.success(self.request, 'Room updated successfully!')
        return super().form_valid(form)


class RoomDeleteView(LoginRequiredMixin, DeleteView):
    model = Room
    template_name = 'household/room_confirm_delete.html'
    success_url = reverse_lazy('room_list')
    
    def get_object(self, queryset=None):
        room = super().get_object(queryset)
        require_house_access(self.request.user, room.house, require_edit=True)
        return room

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Room deleted successfully!')
        return super().delete(request, *args, **kwargs)


class ApplianceListView(LoginRequiredMixin, ListView):
    model = Appliance
    template_name = 'household/appliance_list.html'
    context_object_name = 'appliances'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Appliance.objects.all()
        house_id = self.request.GET.get('house')
        return filter_by_user_house(queryset, self.request.user, house_id)


class ApplianceDetailView(LoginRequiredMixin, DetailView):
    model = Appliance
    template_name = 'household/appliance_detail.html'
    context_object_name = 'appliance'
    
    def get_object(self, queryset=None):
        appliance = super().get_object(queryset)
        require_house_access(self.request.user, appliance.house)
        return appliance


class ApplianceCreateView(LoginRequiredMixin, CreateView):
    model = Appliance
    form_class = ApplianceForm
    template_name = 'household/appliance_form.html'
    success_url = reverse_lazy('appliance_list')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['house'].queryset = get_user_editable_houses(self.request.user)
        # Filter rooms to only those in user's houses
        form.fields['room'].queryset = filter_by_user_house(Room.objects.all(), self.request.user)
        return form

    def form_valid(self, form):
        require_house_access(self.request.user, form.cleaned_data['house'], require_edit=True)
        # Verify room belongs to the same house
        if form.cleaned_data.get('room') and form.cleaned_data['room'].house != form.cleaned_data['house']:
            form.add_error('room', 'Room must belong to the selected house.')
            return self.form_invalid(form)
        messages.success(self.request, 'Appliance created successfully!')
        return super().form_valid(form)


class ApplianceUpdateView(LoginRequiredMixin, UpdateView):
    model = Appliance
    form_class = ApplianceForm
    template_name = 'household/appliance_form.html'
    success_url = reverse_lazy('appliance_list')

    def get_object(self, queryset=None):
        appliance = super().get_object(queryset)
        require_house_access(self.request.user, appliance.house, require_edit=True)
        return appliance

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['house'].queryset = get_user_editable_houses(self.request.user)
        form.fields['room'].queryset = filter_by_user_house(Room.objects.all(), self.request.user)
        return form

    def form_valid(self, form):
        require_house_access(self.request.user, form.cleaned_data['house'], require_edit=True)
        if form.cleaned_data.get('room') and form.cleaned_data['room'].house != form.cleaned_data['house']:
            form.add_error('room', 'Room must belong to the selected house.')
            return self.form_invalid(form)
        messages.success(self.request, 'Appliance updated successfully!')
        return super().form_valid(form)


class ApplianceDeleteView(LoginRequiredMixin, DeleteView):
    model = Appliance
    template_name = 'household/appliance_confirm_delete.html'
    success_url = reverse_lazy('appliance_list')
    
    def get_object(self, queryset=None):
        appliance = super().get_object(queryset)
        require_house_access(self.request.user, appliance.house, require_edit=True)
        return appliance

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Appliance deleted successfully!')
        return super().delete(request, *args, **kwargs)


class VendorListView(LoginRequiredMixin, ListView):
    model = Vendor
    template_name = 'household/vendor_list.html'
    context_object_name = 'vendors'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Vendor.objects.all()
        house_id = self.request.GET.get('house')
        return filter_by_user_house(queryset, self.request.user, house_id)


class VendorDetailView(LoginRequiredMixin, DetailView):
    model = Vendor
    template_name = 'household/vendor_detail.html'
    context_object_name = 'vendor'
    
    def get_object(self, queryset=None):
        vendor = super().get_object(queryset)
        require_house_access(self.request.user, vendor.house)
        return vendor


class VendorCreateView(LoginRequiredMixin, CreateView):
    model = Vendor
    template_name = 'household/vendor_form.html'
    fields = ['house', 'name', 'contact_person', 'email', 'phone', 'address', 
              'website', 'service_type', 'notes']
    success_url = reverse_lazy('vendor_list')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['house'].queryset = get_user_editable_houses(self.request.user)
        return form

    def form_valid(self, form):
        require_house_access(self.request.user, form.cleaned_data['house'], require_edit=True)
        messages.success(self.request, 'Vendor created successfully!')
        return super().form_valid(form)


class VendorUpdateView(LoginRequiredMixin, UpdateView):
    model = Vendor
    template_name = 'household/vendor_form.html'
    fields = ['house', 'name', 'contact_person', 'email', 'phone', 'address', 
              'website', 'service_type', 'notes']
    success_url = reverse_lazy('vendor_list')

    def get_object(self, queryset=None):
        vendor = super().get_object(queryset)
        require_house_access(self.request.user, vendor.house, require_edit=True)
        return vendor

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['house'].queryset = get_user_editable_houses(self.request.user)
        return form

    def form_valid(self, form):
        require_house_access(self.request.user, form.cleaned_data['house'], require_edit=True)
        messages.success(self.request, 'Vendor updated successfully!')
        return super().form_valid(form)


class VendorDeleteView(LoginRequiredMixin, DeleteView):
    model = Vendor
    template_name = 'household/vendor_confirm_delete.html'
    success_url = reverse_lazy('vendor_list')
    
    def get_object(self, queryset=None):
        vendor = super().get_object(queryset)
        require_house_access(self.request.user, vendor.house, require_edit=True)
        return vendor

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Vendor deleted successfully!')
        return super().delete(request, *args, **kwargs)


class InvoiceListView(LoginRequiredMixin, ListView):
    model = Invoice
    template_name = 'household/invoice_list.html'
    context_object_name = 'invoices'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Invoice.objects.all()
        house_id = self.request.GET.get('house')
        return filter_by_user_house(queryset, self.request.user, house_id)


class InvoiceDetailView(LoginRequiredMixin, DetailView):
    model = Invoice
    template_name = 'household/invoice_detail.html'
    context_object_name = 'invoice'
    
    def get_object(self, queryset=None):
        invoice = super().get_object(queryset)
        require_house_access(self.request.user, invoice.house)
        return invoice
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['line_items'] = self.object.line_items.all()
        return context


class InvoiceCreateView(LoginRequiredMixin, CreateView):
    model = Invoice
    form_class = InvoiceForm
    template_name = 'household/invoice_form.html'
    success_url = reverse_lazy('invoice_list')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['house'].queryset = get_user_editable_houses(self.request.user)
        # Filter vendors and appliances to user's houses
        form.fields['vendor'].queryset = filter_by_user_house(Vendor.objects.all(), self.request.user)
        form.fields['related_appliance'].queryset = filter_by_user_house(Appliance.objects.all(), self.request.user)
        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get house from form data or existing object
        house = None
        if self.request.POST and 'house' in self.request.POST:
            try:
                house_id = int(self.request.POST['house'])
                from .models import House
                house = House.objects.get(pk=house_id)
            except (ValueError, House.DoesNotExist):
                pass
        elif hasattr(self, 'object') and self.object:
            house = self.object.house
        
        # Create a temporary invoice instance for the formset if needed
        invoice_instance = None
        if hasattr(self, 'object') and self.object:
            invoice_instance = self.object
        elif house:
            # Create a temporary unsaved invoice for the formset
            invoice_instance = Invoice(house=house)
        
        if self.request.POST:
            context['line_items'] = InvoiceLineItemFormSet(self.request.POST, instance=invoice_instance)
        else:
            context['line_items'] = InvoiceLineItemFormSet(instance=invoice_instance)
        
        # Update formset forms to have house context
        if house and context.get('line_items'):
            for form in context['line_items'].forms:
                form.fields['rooms'].queryset = house.rooms.all()
                form.fields['appliances'].queryset = house.appliances.all()
        
        return context

    def form_valid(self, form):
        house = form.cleaned_data['house']
        require_house_access(self.request.user, house, require_edit=True)
        # Verify vendor and appliance belong to the same house
        if form.cleaned_data.get('vendor') and form.cleaned_data['vendor'].house != house:
            form.add_error('vendor', 'Vendor must belong to the selected house.')
            return self.form_invalid(form)
        if form.cleaned_data.get('related_appliance') and form.cleaned_data['related_appliance'].house != house:
            form.add_error('related_appliance', 'Appliance must belong to the selected house.')
            return self.form_invalid(form)
        
        # Check if line items are provided
        line_items = InvoiceLineItemFormSet(self.request.POST, instance=None)
        # Update formset forms to have house context for validation
        for line_form in line_items.forms:
            if house:
                line_form.fields['rooms'].queryset = house.rooms.all()
                line_form.fields['appliances'].queryset = house.appliances.all()
        
        # Validate line items first
        if line_items.is_valid():
            # Check if any line items have data (not deleted and have required fields)
            has_line_items = False
            for line_form in line_items.forms:
                if line_form.cleaned_data and not line_form.cleaned_data.get('DELETE', False):
                    # Check if line item has at least description and unit_price
                    if (line_form.cleaned_data.get('description') and 
                        line_form.cleaned_data.get('unit_price')):
                        has_line_items = True
                        break
            
            # If no line items and no amount provided, require amount
            if not has_line_items and not form.cleaned_data.get('amount'):
                form.add_error('amount', 'Either provide line items or enter an amount.')
                return self.form_invalid(form)
            
            # If line items exist but no amount provided, set amount to 0 (will be calculated)
            if has_line_items and not form.cleaned_data.get('amount'):
                form.cleaned_data['amount'] = 0
        else:
            # If line items have errors, show them
            messages.error(self.request, 'There were errors in the line items. Please correct them.')
            return self.form_invalid(form)
        
        # Save invoice first
        response = super().form_valid(form)
        
        # Save line items after invoice is saved
        line_items.instance = self.object
        line_items.save()
        
        # Update invoice totals from line items
        self.object.save()  # This will recalculate from line items
        messages.success(self.request, 'Invoice created successfully!')
        
        return response


class InvoiceUpdateView(LoginRequiredMixin, UpdateView):
    model = Invoice
    form_class = InvoiceForm
    template_name = 'household/invoice_form.html'
    success_url = reverse_lazy('invoice_list')

    def get_object(self, queryset=None):
        invoice = super().get_object(queryset)
        require_house_access(self.request.user, invoice.house, require_edit=True)
        return invoice

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['house'].queryset = get_user_editable_houses(self.request.user)
        form.fields['vendor'].queryset = filter_by_user_house(Vendor.objects.all(), self.request.user)
        form.fields['related_appliance'].queryset = filter_by_user_house(Appliance.objects.all(), self.request.user)
        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['line_items'] = InvoiceLineItemFormSet(self.request.POST, instance=self.object)
        else:
            context['line_items'] = InvoiceLineItemFormSet(instance=self.object)
        return context

    def form_valid(self, form):
        house = form.cleaned_data['house']
        require_house_access(self.request.user, house, require_edit=True)
        if form.cleaned_data.get('vendor') and form.cleaned_data['vendor'].house != house:
            form.add_error('vendor', 'Vendor must belong to the selected house.')
            return self.form_invalid(form)
        if form.cleaned_data.get('related_appliance') and form.cleaned_data['related_appliance'].house != house:
            form.add_error('related_appliance', 'Appliance must belong to the selected house.')
            return self.form_invalid(form)
        
        # Save invoice first
        response = super().form_valid(form)
        
        # Handle line items
        line_items = InvoiceLineItemFormSet(self.request.POST, instance=self.object)
        # Update formset forms to have house context for validation
        for form in line_items.forms:
            if house:
                form.fields['rooms'].queryset = house.rooms.all()
                form.fields['appliances'].queryset = house.appliances.all()
        
        if line_items.is_valid():
            line_items.save()
            # Update invoice totals from line items
            self.object.save()  # This will recalculate from line items
            messages.success(self.request, 'Invoice updated successfully!')
        else:
            messages.error(self.request, 'There were errors in the line items. Please correct them.')
            return self.form_invalid(form)
        
        return response


class InvoiceDeleteView(LoginRequiredMixin, DeleteView):
    model = Invoice
    template_name = 'household/invoice_confirm_delete.html'
    success_url = reverse_lazy('invoice_list')
    
    def get_object(self, queryset=None):
        invoice = super().get_object(queryset)
        require_house_access(self.request.user, invoice.house, require_edit=True)
        return invoice

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Invoice deleted successfully!')
        return super().delete(request, *args, **kwargs)


# Manual Search and Maintenance Views

@login_required
@require_http_methods(["POST"])
def search_manual(request, pk):
    """Search for appliance manual online."""
    from .utils import is_valid_pdf_url
    
    appliance = get_object_or_404(Appliance, pk=pk)
    require_house_access(request.user, appliance.house, require_edit=True)
    
    if not appliance.brand and not appliance.model_number:
        messages.error(request, 'Brand or Model Number is required to search for manual.')
        return redirect('appliance_detail', pk=pk)
    
    try:
        result = search_manual_online(appliance.brand, appliance.model_number, appliance.name)
        if result:
            url = result.get('url')
            # Check if this is a support page URL (non-PDF) that should be handled differently
            if result.get('note'):
                # This is a support page URL, not a direct PDF
                support_url = url
                messages.info(request, 
                    f'Found manufacturer support page: {support_url}. '
                    f'Please search for model {appliance.model_number} on that page to find the manual PDF.')
                return redirect('appliance_detail', pk=pk)
            
            # Double-check URL is valid PDF before saving
            if url and is_valid_pdf_url(url):
                appliance.manual_url = url
                appliance.save()
                messages.success(request, f'Manual found! URL saved. You can download it now.')
            else:
                messages.warning(request, 'Found a link but it was not a valid PDF URL. Try uploading manually.')
        else:
            messages.warning(request, 'No manual found online. Try uploading manually.')
    except Exception as e:
        messages.error(request, f'Error searching for manual: {str(e)}')
    
    return redirect('appliance_detail', pk=pk)


@login_required
@require_http_methods(["POST"])
def download_manual(request, pk):
    """Download manual from URL and save to appliance."""
    appliance = get_object_or_404(Appliance, pk=pk)
    require_house_access(request.user, appliance.house, require_edit=True)
    
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


@login_required
@require_http_methods(["POST"])
def extract_maintenance(request, pk):
    """Extract maintenance tasks from uploaded manual PDF."""
    appliance = get_object_or_404(Appliance, pk=pk)
    require_house_access(request.user, appliance.house, require_edit=True)
    
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

class MaintenanceTaskListView(LoginRequiredMixin, ListView):
    model = MaintenanceTask
    template_name = 'household/maintenance_task_list.html'
    context_object_name = 'tasks'
    paginate_by = 20

    def get_queryset(self):
        queryset = MaintenanceTask.objects.filter(is_active=True)
        # Filter by user's houses
        queryset = filter_by_user_house(queryset, self.request.user, self.request.GET.get('house'))
        # Filter by appliance if specified
        appliance_id = self.request.GET.get('appliance')
        if appliance_id:
            appliance = get_object_or_404(Appliance, pk=appliance_id)
            require_house_access(self.request.user, appliance.house)
            queryset = queryset.filter(appliance_id=appliance_id)
        return queryset.order_by('next_due', 'appliance')


class MaintenanceTaskDetailView(LoginRequiredMixin, DetailView):
    model = MaintenanceTask
    template_name = 'household/maintenance_task_detail.html'
    context_object_name = 'task'
    
    def get_object(self, queryset=None):
        task = super().get_object(queryset)
        require_house_access(self.request.user, task.appliance.house)
        return task


class MaintenanceTaskCreateView(LoginRequiredMixin, CreateView):
    model = MaintenanceTask
    form_class = MaintenanceTaskForm
    template_name = 'household/maintenance_task_form.html'
    
    def get_success_url(self):
        return reverse_lazy('appliance_detail', kwargs={'pk': self.object.appliance.pk})
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['appliance'].queryset = filter_by_user_house(Appliance.objects.all(), self.request.user)
        return form

    def form_valid(self, form):
        appliance = form.cleaned_data['appliance']
        require_house_access(self.request.user, appliance.house, require_edit=True)
        messages.success(self.request, 'Maintenance task created successfully!')
        return super().form_valid(form)


class MaintenanceTaskUpdateView(LoginRequiredMixin, UpdateView):
    model = MaintenanceTask
    form_class = MaintenanceTaskForm
    template_name = 'household/maintenance_task_form.html'
    
    def get_success_url(self):
        return reverse_lazy('appliance_detail', kwargs={'pk': self.object.appliance.pk})
    
    def get_object(self, queryset=None):
        task = super().get_object(queryset)
        require_house_access(self.request.user, task.appliance.house, require_edit=True)
        return task

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['appliance'].queryset = filter_by_user_house(Appliance.objects.all(), self.request.user)
        return form

    def form_valid(self, form):
        appliance = form.cleaned_data['appliance']
        require_house_access(self.request.user, appliance.house, require_edit=True)
        # Recalculate next_due if last_performed changed
        if 'last_performed' in form.changed_data:
            task = form.save(commit=False)
            if task.last_performed:
                task.next_due = task.calculate_next_due()
            task.save()
        messages.success(self.request, 'Maintenance task updated successfully!')
        return super().form_valid(form)


class MaintenanceTaskDeleteView(LoginRequiredMixin, DeleteView):
    model = MaintenanceTask
    template_name = 'household/maintenance_task_confirm_delete.html'
    
    def get_success_url(self):
        return reverse_lazy('appliance_detail', kwargs={'pk': self.object.appliance.pk})
    
    def get_object(self, queryset=None):
        task = super().get_object(queryset)
        require_house_access(self.request.user, task.appliance.house, require_edit=True)
        return task
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Maintenance task deleted successfully!')
        return super().delete(request, *args, **kwargs)


@login_required
@require_http_methods(["POST"])
def mark_maintenance_complete(request, pk):
    """Mark a maintenance task as complete and update next due date."""
    task = get_object_or_404(MaintenanceTask, pk=pk)
    require_house_access(request.user, task.appliance.house, require_edit=True)
    task.last_performed = date.today()
    task.next_due = task.calculate_next_due()
    task.save()
    messages.success(request, f'Maintenance task "{task.task_name}" marked as complete!')
    return redirect('appliance_detail', pk=task.appliance.pk)


@login_required
@require_http_methods(["POST"])
def extract_info_from_label(request):
    """Extract appliance information from uploaded label image."""
    # Note: This view doesn't require a house check as it's used during appliance creation
    # The house will be set when the appliance is saved
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



