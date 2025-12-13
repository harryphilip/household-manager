"""
Permission helper functions for house-based access control.
"""
from django.db import models
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from .models import House


def get_user_houses(user):
    """
    Get all houses that a user has access to (as owner, admin, or viewer).
    Returns a queryset of House objects.
    """
    if not user or not user.is_authenticated:
        return House.objects.none()
    
    # Get houses where user is owner, admin, or viewer
    return House.objects.filter(
        models.Q(owners=user) | 
        models.Q(admins=user) | 
        models.Q(viewers=user)
    ).distinct()


def get_user_editable_houses(user):
    """
    Get all houses that a user can edit (as owner or admin).
    Returns a queryset of House objects.
    """
    if not user or not user.is_authenticated:
        return House.objects.none()
    
    return House.objects.filter(
        models.Q(owners=user) | 
        models.Q(admins=user)
    ).distinct()


def require_house_access(user, house, require_edit=False):
    """
    Check if user has access to a house. Raises PermissionDenied if not.
    
    Args:
        user: The user to check
        house: House object or house ID
        require_edit: If True, requires edit access (owner or admin), not just view
    
    Raises:
        PermissionDenied: If user doesn't have required access
    """
    if not user or not user.is_authenticated:
        raise PermissionDenied("You must be logged in to access this house.")
    
    if isinstance(house, int):
        house = get_object_or_404(House, pk=house)
    
    if require_edit:
        if not house.can_user_edit(user):
            raise PermissionDenied("You don't have permission to edit this house.")
    else:
        if not house.can_user_view(user):
            raise PermissionDenied("You don't have permission to view this house.")


def filter_by_user_house(queryset, user, house_id=None):
    """
    Filter a queryset to only include objects from houses the user can access.
    
    Args:
        queryset: QuerySet to filter (must have a 'house' ForeignKey or 'appliance__house')
        user: The user to filter for
        house_id: Optional house ID to filter to a specific house
    
    Returns:
        Filtered QuerySet
    """
    if not user or not user.is_authenticated:
        return queryset.none()
    
    # Get houses user can access
    accessible_houses = get_user_houses(user)
    
    if house_id:
        # Filter to specific house if provided
        accessible_houses = accessible_houses.filter(pk=house_id)
        if not accessible_houses.exists():
            return queryset.none()
    
    # Check if queryset model has 'house' field directly
    model = queryset.model
    if hasattr(model, 'house'):
        # Direct house relationship (Room, Appliance, Vendor, Invoice)
        return queryset.filter(house__in=accessible_houses)
    elif hasattr(model, 'appliance'):
        # Indirect house relationship through appliance (MaintenanceTask)
        return queryset.filter(appliance__house__in=accessible_houses)
    else:
        # No house relationship, return empty queryset
        return queryset.none()

