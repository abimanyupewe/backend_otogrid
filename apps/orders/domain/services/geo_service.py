"""
Geo Matching Domain Service.
Handles spatial queries for mechanics within an absolute radius using PostGIS ST_DWithin with Python Haversine fallback.
"""
import math
from typing import List
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from apps.authentication.data.models import User, UserRole


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates distance between two coordinates in kilometers using Haversine formula."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


class GeoMatchingService:
    """
    Service class handling spatial geo-matching queries for mechanics.
    """

    @staticmethod
    def find_nearby_online_mechanics(
        location_point: Point,
        radius_km: float = 5.0
    ) -> List[User]:
        """
        Scans database for online mechanics within the specified radius in KM.
        """
        try:
            nearby_mechanics = User.objects.filter(
                role=UserRole.MECHANIC,
                is_online=True,
                location_data__isnull=False,
                current_location__distance_lte=(location_point, D(km=radius_km))
            )
            return list(nearby_mechanics)
        except Exception:
            # Fallback to Haversine calculation in memory
            online_mechanics = User.objects.filter(
                role=UserRole.MECHANIC,
                is_online=True,
                location_data__isnull=False
            )
            results = []
            target_lat, target_lon = location_point.y, location_point.x
            for mech in online_mechanics:
                if mech.current_location:
                    dist = haversine_km(target_lat, target_lon, mech.current_location.y, mech.current_location.x)
                    if dist <= radius_km:
                        results.append(mech)
            return results

    @staticmethod
    def find_nearby_active_orders(
        mechanic_location: Point,
        radius_km: float = 5.0
    ):
        """
        Scans database for active 'SEARCHING' orders near a mechanic's location.
        """
        from apps.orders.data.models import Order, OrderStatus

        try:
            return Order.objects.filter(
                status=OrderStatus.SEARCHING,
                location__distance_lte=(mechanic_location, D(km=radius_km))
            ).order_by('-created_at')
        except Exception:
            searching_orders = Order.objects.filter(
                status=OrderStatus.SEARCHING,
                location_data__isnull=False
            ).order_by('-created_at')
            mech_lat, mech_lon = mechanic_location.y, mechanic_location.x
            nearby_ids = []
            for order in searching_orders:
                if order.location:
                    dist = haversine_km(mech_lat, mech_lon, order.location.y, order.location.x)
                    if dist <= radius_km:
                        nearby_ids.append(order.id)
            return Order.objects.filter(id__in=nearby_ids).order_by('-created_at')
