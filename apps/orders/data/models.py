"""
Orders Data Models.
Defines Order model with spatial coordinates and Order State Machine statuses.
"""
from typing import Optional
from django.db import models
from django.conf import settings
from django.contrib.gis.geos import Point


class OrderStatus(models.TextChoices):
    """
    Order State Machine choices.
    """
    SEARCHING = 'SEARCHING', 'Mencari Mekanik'
    ACCEPTED = 'ACCEPTED', 'Diterima Mekanik'
    ON_THE_WAY = 'ON_THE_WAY', 'Mekanik Dalam Perjalanan'
    ARRIVED = 'ARRIVED', 'Mekanik Tiba di Lokasi'
    WORKING = 'WORKING', 'Proses Perbaikan'
    COMPLETED = 'COMPLETED', 'Selesai'
    CANCELLED = 'CANCELLED', 'Dibatalkan'


class Order(models.Model):
    """
    Emergency Mechanic Order Model.
    Tracks customer emergency requests, mechanic assignment, state machine status, and AI triage data.
    """
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='customer_orders',
        help_text="Pelanggan yang membuat pesanan"
    )
    mechanic = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='mechanic_orders',
        help_text="Mekanik yang menerima pesanan"
    )
    
    # Store coordinates in JSON field compatible with standard PostgreSQL and PostGIS
    location_data = models.JSONField(
        help_text="Koordinat lokasi darurat ({'lat': float, 'lng': float})"
    )
    location_address = models.TextField(
        blank=True,
        null=True,
        help_text="Alamat / petunjuk lokasi darurat"
    )
    complaint_text = models.TextField(
        help_text="Deskripsi keluhan atau kendala kendaraan"
    )
    ai_triage_result = models.JSONField(
        blank=True,
        null=True,
        help_text="Hasil analisis & diagnosa teknis dari Google Gemini AI"
    )
    status = models.CharField(
        max_length=20,
        choices=OrderStatus.choices,
        default=OrderStatus.SEARCHING,
        db_index=True,
        help_text="Status pesanan dalam state machine"
    )
    total_fee = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Total biaya perbaikan"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def location(self) -> Optional[Point]:
        """Returns spatial Point object (x=lng, y=lat) from location_data."""
        if self.location_data and isinstance(self.location_data, dict):
            lat = self.location_data.get('lat')
            lng = self.location_data.get('lng')
            if lat is not None and lng is not None:
                return Point(float(lng), float(lat), srid=4326)
        return None

    @location.setter
    def location(self, value: Optional[Point]):
        """Sets location_data from a Point object or tuple/list."""
        if value is None:
            self.location_data = {}
        elif hasattr(value, 'x') and hasattr(value, 'y'):
            self.location_data = {'lat': float(value.y), 'lng': float(value.x)}
        elif isinstance(value, (list, tuple)) and len(value) == 2:
            self.location_data = {'lat': float(value[1]), 'lng': float(value[0])}

    class Meta:
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f"Order #{self.id} - {self.customer.username} [{self.get_status_display()}]"
