"""
Order Service Domain Layer.
Handles Order State Machine logic, transactional concurrency control with select_for_update, and order creation.
"""
from typing import Tuple, List, Optional
from django.db import transaction
from django.contrib.gis.geos import Point
from rest_framework.exceptions import ValidationError, PermissionDenied

from apps.authentication.data.models import User, UserRole
from apps.orders.data.models import Order, OrderStatus
from apps.orders.domain.services.ai_service import AITriageService
from apps.orders.domain.services.geo_service import GeoMatchingService


class OrderService:
    """
    Service class handling core order operations and State Machine transitions.
    """

    VALID_TRANSITIONS = {
        OrderStatus.SEARCHING: [OrderStatus.ACCEPTED, OrderStatus.CANCELLED],
        OrderStatus.ACCEPTED: [OrderStatus.ON_THE_WAY, OrderStatus.CANCELLED],
        OrderStatus.ON_THE_WAY: [OrderStatus.ARRIVED, OrderStatus.CANCELLED],
        OrderStatus.ARRIVED: [OrderStatus.WORKING, OrderStatus.CANCELLED],
        OrderStatus.WORKING: [OrderStatus.COMPLETED, OrderStatus.CANCELLED],
        OrderStatus.COMPLETED: [],
        OrderStatus.CANCELLED: [],
    }

    @classmethod
    def create_order(
        cls,
        customer: User,
        latitude: float,
        longitude: float,
        location_address: str,
        complaint_text: str
    ) -> Tuple[Order, int]:
        """
        Creates emergency mechanic order, triggers AI triage, and scans nearby mechanics.

        Args:
            customer (User): The requesting customer.
            latitude (float): GPS Latitude.
            longitude (float): GPS Longitude.
            location_address (str): Readable address string.
            complaint_text (str): User complaint description.

        Returns:
            Tuple[Order, int]: Created Order object and count of nearby mechanics scanned.
        """
        location_point = Point(longitude, latitude, srid=4326)

        # Trigger AI Diagnosis
        ai_triage = AITriageService.diagnose_complaint(complaint_text)

        order = Order.objects.create(
            customer=customer,
            location=location_point,
            location_address=location_address,
            complaint_text=complaint_text,
            ai_triage_result=ai_triage,
            status=OrderStatus.SEARCHING
        )

        nearby_mechanics = GeoMatchingService.find_nearby_online_mechanics(location_point, radius_km=5.0)

        return order, len(nearby_mechanics)

    @classmethod
    def accept_order(cls, order_id: int, mechanic: User) -> Order:
        """
        Mechanic accepts an open order using SELECT FOR UPDATE concurrency control.

        Args:
            order_id (int): ID of order to accept.
            mechanic (User): Mechanic accepting the order.

        Returns:
            Order: Updated order instance.
        """
        if mechanic.role != UserRole.MECHANIC:
            raise PermissionDenied("Hanya pengguna bertipe MEKANIK yang dapat menerima pesanan.")

        with transaction.atomic():
            # Lock order row to prevent race condition
            try:
                order = Order.objects.select_for_update().get(id=order_id)
            except Order.DoesNotExist:
                raise ValidationError("Pesanan tidak ditemukan.")

            if order.status != OrderStatus.SEARCHING:
                raise ValidationError("Pesanan ini sudah diambil oleh mekanik lain atau telah dibatalkan.")

            # Check if mechanic already has an active order
            active_order = Order.objects.filter(
                mechanic=mechanic,
                status__in=[OrderStatus.ACCEPTED, OrderStatus.ON_THE_WAY, OrderStatus.ARRIVED, OrderStatus.WORKING]
            ).first()

            if active_order:
                raise ValidationError("Anda masih memiliki pesanan aktif yang belum diselesaikan.")

            order.mechanic = mechanic
            order.status = OrderStatus.ACCEPTED
            order.save()

            return order

    @classmethod
    def update_order_status(
        cls,
        order_id: int,
        user: User,
        new_status: str,
        total_fee: Optional[float] = None
    ) -> Order:
        """
        Updates order status following strict State Machine transition rules.

        Args:
            order_id (int): Target order ID.
            user (User): Requesting user (Customer or Mechanic).
            new_status (str): Target OrderStatus choice.
            total_fee (Optional[float]): Final billing fee upon completion.

        Returns:
            Order: Updated order object.
        """
        with transaction.atomic():
            try:
                order = Order.objects.select_for_update().get(id=order_id)
            except Order.DoesNotExist:
                raise ValidationError("Pesanan tidak ditemukan.")

            # Authorization Check
            if user != order.customer and user != order.mechanic:
                raise PermissionDenied("Anda tidak memiliki akses ke pesanan ini.")

            # Validate State Machine Transition
            allowed_next_states = cls.VALID_TRANSITIONS.get(order.status, [])
            if new_status not in allowed_next_states:
                raise ValidationError(
                    f"Transisi status dari '{order.status}' ke '{new_status}' tidak valid."
                )

            order.status = new_status
            if new_status == OrderStatus.COMPLETED and total_fee is not None:
                order.total_fee = total_fee

            order.save()
            return order
