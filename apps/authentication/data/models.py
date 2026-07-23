"""
Authentication Data Models.
Defines User model with spatial location tracking for mechanics.
"""
from typing import Optional
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.gis.geos import Point


class UserRole(models.TextChoices):
    """
    Role choices for system users.
    """
    CUSTOMER = 'CUSTOMER', 'Pelanggan'
    MECHANIC = 'MECHANIC', 'Mitra Mekanik'


class User(AbstractUser):
    """
    Custom User Model extending Django AbstractUser.
    Includes spatial PointField (or Point wrapper) for mechanic location tracking.
    """
    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.CUSTOMER,
        help_text="Role pengguna (CUSTOMER / MECHANIC)"
    )
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="Nomor Telepon/WhatsApp aktif"
    )
    full_name = models.CharField(
        max_length=150,
        blank=True,
        null=True,
        help_text="Nama Lengkap Pengguna"
    )
    is_online = models.BooleanField(
        default=False,
        help_text="Status online ketersediaan mekanik"
    )
    
    # Store coordinates in JSON field compatible with standard PostgreSQL and PostGIS
    location_data = models.JSONField(
        blank=True,
        null=True,
        help_text="Koordinat lokasi ({'lat': float, 'lng': float})"
    )

    @property
    def current_location(self) -> Optional[Point]:
        """Returns spatial Point object (x=lng, y=lat) from location_data."""
        if self.location_data and isinstance(self.location_data, dict):
            lat = self.location_data.get('lat')
            lng = self.location_data.get('lng')
            if lat is not None and lng is not None:
                return Point(float(lng), float(lat), srid=4326)
        return None

    @current_location.setter
    def current_location(self, value: Optional[Point]):
        """Sets location_data from a Point object or tuple/list."""
        if value is None:
            self.location_data = None
        elif hasattr(value, 'x') and hasattr(value, 'y'):
            self.location_data = {'lat': float(value.y), 'lng': float(value.x)}
        elif isinstance(value, (list, tuple)) and len(value) == 2:
            self.location_data = {'lat': float(value[1]), 'lng': float(value[0])}

    def __str__(self) -> str:
        return f"{self.username} ({self.get_role_display()})"
