"""
Tests for house-based permissions.
"""
from django.test import TestCase
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from household.models import House, Room, Appliance, Vendor, Invoice
from household.permissions import (
    get_user_houses, get_user_editable_houses, require_house_access,
    filter_by_user_house
)


class PermissionHelpersTest(TestCase):
    """Test cases for permission helper functions."""
    
    def setUp(self):
        """Set up test data."""
        self.owner = User.objects.create_user('owner', 'owner@example.com', 'password')
        self.admin = User.objects.create_user('admin', 'admin@example.com', 'password')
        self.viewer = User.objects.create_user('viewer', 'viewer@example.com', 'password')
        self.other_user = User.objects.create_user('other', 'other@example.com', 'password')
        
        self.house1 = House.objects.create(address="123 Owner Street")
        self.house1.owners.add(self.owner)
        
        self.house2 = House.objects.create(address="456 Admin Street")
        self.house2.admins.add(self.admin)
        
        self.house3 = House.objects.create(address="789 Viewer Street")
        self.house3.viewers.add(self.viewer)
        
        self.house4 = House.objects.create(address="999 Other Street")
        self.house4.owners.add(self.other_user)
    
    def test_get_user_houses(self):
        """Test getting all houses user can access."""
        owner_houses = get_user_houses(self.owner)
        self.assertEqual(owner_houses.count(), 1)
        self.assertIn(self.house1, owner_houses)
        
        admin_houses = get_user_houses(self.admin)
        self.assertEqual(admin_houses.count(), 1)
        self.assertIn(self.house2, admin_houses)
        
        viewer_houses = get_user_houses(self.viewer)
        self.assertEqual(viewer_houses.count(), 1)
        self.assertIn(self.house3, viewer_houses)
        
        other_houses = get_user_houses(self.other_user)
        self.assertEqual(other_houses.count(), 1)
        self.assertIn(self.house4, other_houses)
    
    def test_get_user_editable_houses(self):
        """Test getting houses user can edit."""
        owner_editable = get_user_editable_houses(self.owner)
        self.assertEqual(owner_editable.count(), 1)
        self.assertIn(self.house1, owner_editable)
        
        admin_editable = get_user_editable_houses(self.admin)
        self.assertEqual(admin_editable.count(), 1)
        self.assertIn(self.house2, admin_editable)
        
        viewer_editable = get_user_editable_houses(self.viewer)
        self.assertEqual(viewer_editable.count(), 0)  # Viewers can't edit
    
    def test_require_house_access_view(self):
        """Test require_house_access for view permission."""
        # Owner can view
        require_house_access(self.owner, self.house1)
        
        # Admin can view
        require_house_access(self.admin, self.house2)
        
        # Viewer can view
        require_house_access(self.viewer, self.house3)
        
        # Other user cannot view
        with self.assertRaises(PermissionDenied):
            require_house_access(self.other_user, self.house1)
    
    def test_require_house_access_edit(self):
        """Test require_house_access for edit permission."""
        # Owner can edit
        require_house_access(self.owner, self.house1, require_edit=True)
        
        # Admin can edit
        require_house_access(self.admin, self.house2, require_edit=True)
        
        # Viewer cannot edit
        with self.assertRaises(PermissionDenied):
            require_house_access(self.viewer, self.house3, require_edit=True)
        
        # Other user cannot edit
        with self.assertRaises(PermissionDenied):
            require_house_access(self.other_user, self.house1, require_edit=True)
    
    def test_filter_by_user_house(self):
        """Test filtering querysets by user's houses."""
        # Create rooms in different houses
        room1 = Room.objects.create(house=self.house1, name="Room 1")
        room2 = Room.objects.create(house=self.house2, name="Room 2")
        room3 = Room.objects.create(house=self.house3, name="Room 3")
        room4 = Room.objects.create(house=self.house4, name="Room 4")
        
        # Owner should only see room1
        owner_rooms = filter_by_user_house(Room.objects.all(), self.owner)
        self.assertEqual(owner_rooms.count(), 1)
        self.assertIn(room1, owner_rooms)
        self.assertNotIn(room2, owner_rooms)
        
        # Admin should only see room2
        admin_rooms = filter_by_user_house(Room.objects.all(), self.admin)
        self.assertEqual(admin_rooms.count(), 1)
        self.assertIn(room2, admin_rooms)
        
        # Viewer should only see room3
        viewer_rooms = filter_by_user_house(Room.objects.all(), self.viewer)
        self.assertEqual(viewer_rooms.count(), 1)
        self.assertIn(room3, viewer_rooms)
    
    def test_filter_by_user_house_specific_house(self):
        """Test filtering to a specific house."""
        room1 = Room.objects.create(house=self.house1, name="Room 1")
        room2 = Room.objects.create(house=self.house2, name="Room 2")
        
        # Filter to house1
        filtered = filter_by_user_house(Room.objects.all(), self.owner, house_id=self.house1.pk)
        self.assertEqual(filtered.count(), 1)
        self.assertIn(room1, filtered)
        
        # Filter to house2 (owner doesn't have access)
        filtered = filter_by_user_house(Room.objects.all(), self.owner, house_id=self.house2.pk)
        self.assertEqual(filtered.count(), 0)
    
    def test_filter_by_user_house_unauthenticated(self):
        """Test filtering for unauthenticated user."""
        Room.objects.create(house=self.house1, name="Room 1")
        
        filtered = filter_by_user_house(Room.objects.all(), None)
        self.assertEqual(filtered.count(), 0)
        
        unauthenticated_user = User.objects.create_user('unauth', 'unauth@example.com', 'password')
        # User exists but not assigned to any house
        filtered = filter_by_user_house(Room.objects.all(), unauthenticated_user)
        self.assertEqual(filtered.count(), 0)


class HouseModelPermissionsTest(TestCase):
    """Test cases for House model permission methods."""
    
    def setUp(self):
        """Set up test data."""
        self.owner = User.objects.create_user('owner', 'owner@example.com', 'password')
        self.admin = User.objects.create_user('admin', 'admin@example.com', 'password')
        self.viewer = User.objects.create_user('viewer', 'viewer@example.com', 'password')
        self.other_user = User.objects.create_user('other', 'other@example.com', 'password')
        
        self.house = House.objects.create(address="123 Test Street")
        self.house.owners.add(self.owner)
        self.house.admins.add(self.admin)
        self.house.viewers.add(self.viewer)
    
    def test_can_user_view(self):
        """Test can_user_view method."""
        self.assertTrue(self.house.can_user_view(self.owner))
        self.assertTrue(self.house.can_user_view(self.admin))
        self.assertTrue(self.house.can_user_view(self.viewer))
        self.assertFalse(self.house.can_user_view(self.other_user))
        self.assertFalse(self.house.can_user_view(None))
    
    def test_can_user_edit(self):
        """Test can_user_edit method."""
        self.assertTrue(self.house.can_user_edit(self.owner))
        self.assertTrue(self.house.can_user_edit(self.admin))
        self.assertFalse(self.house.can_user_edit(self.viewer))
        self.assertFalse(self.house.can_user_edit(self.other_user))
        self.assertFalse(self.house.can_user_edit(None))
    
    def test_can_user_delete(self):
        """Test can_user_delete method."""
        self.assertTrue(self.house.can_user_delete(self.owner))
        self.assertFalse(self.house.can_user_delete(self.admin))
        self.assertFalse(self.house.can_user_delete(self.viewer))
        self.assertFalse(self.house.can_user_delete(self.other_user))
        self.assertFalse(self.house.can_user_delete(None))

