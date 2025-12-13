from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    
    # Room URLs
    path('rooms/', views.RoomListView.as_view(), name='room_list'),
    path('rooms/<int:pk>/', views.RoomDetailView.as_view(), name='room_detail'),
    path('rooms/create/', views.RoomCreateView.as_view(), name='room_create'),
    path('rooms/<int:pk>/update/', views.RoomUpdateView.as_view(), name='room_update'),
    path('rooms/<int:pk>/delete/', views.RoomDeleteView.as_view(), name='room_delete'),
    
    # Appliance URLs
    path('appliances/', views.ApplianceListView.as_view(), name='appliance_list'),
    path('appliances/<int:pk>/', views.ApplianceDetailView.as_view(), name='appliance_detail'),
    path('appliances/create/', views.ApplianceCreateView.as_view(), name='appliance_create'),
    path('appliances/<int:pk>/update/', views.ApplianceUpdateView.as_view(), name='appliance_update'),
    path('appliances/<int:pk>/delete/', views.ApplianceDeleteView.as_view(), name='appliance_delete'),
    
    # Vendor URLs
    path('vendors/', views.VendorListView.as_view(), name='vendor_list'),
    path('vendors/<int:pk>/', views.VendorDetailView.as_view(), name='vendor_detail'),
    path('vendors/create/', views.VendorCreateView.as_view(), name='vendor_create'),
    path('vendors/<int:pk>/update/', views.VendorUpdateView.as_view(), name='vendor_update'),
    path('vendors/<int:pk>/delete/', views.VendorDeleteView.as_view(), name='vendor_delete'),
    
    # Invoice URLs
    path('invoices/', views.InvoiceListView.as_view(), name='invoice_list'),
    path('invoices/<int:pk>/', views.InvoiceDetailView.as_view(), name='invoice_detail'),
    path('invoices/create/', views.InvoiceCreateView.as_view(), name='invoice_create'),
    path('invoices/<int:pk>/update/', views.InvoiceUpdateView.as_view(), name='invoice_update'),
    path('invoices/<int:pk>/delete/', views.InvoiceDeleteView.as_view(), name='invoice_delete'),
]



