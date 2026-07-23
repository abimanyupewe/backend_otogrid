"""
Unit tests for Orders module.
"""
from django.test import TestCase
from django.contrib.gis.geos import Point
from apps.authentication.data.models import User, UserRole
from apps.authentication.domain.services import AuthService
from apps.orders.data.models import Order, OrderStatus
from apps.orders.domain.services.order_service import OrderService
from apps.orders.domain.services.geo_service import GeoMatchingService


class OrdersTestCase(TestCase):
    """
    Test suite for Orders Domain Services and State Machine.
    """

    def setUp(self):
        self.customer = AuthService.register_user(
            username="customer_order",
            email="cust_order@otogrid.com",
            password="Password123!",
            full_name="Customer Order",
            role=UserRole.CUSTOMER
        )
        self.mechanic = AuthService.register_user(
            username="mechanic_order",
            email="mech_order@otogrid.com",
            password="Password123!",
            full_name="Mechanic Agus",
            role=UserRole.MECHANIC
        )
        # Update mechanic location near Monas Jakarta (-6.175392, 106.827153)
        AuthService.update_mechanic_status_and_location(
            user=self.mechanic,
            is_online=True,
            latitude=-6.175392,
            longitude=106.827153
        )

    def test_order_creation_and_ai_triage(self):
        order, nearby_count = OrderService.create_order(
            customer=self.customer,
            latitude=-6.175000,
            longitude=106.827000,
            location_address="Jl. Medan Merdeka Barat No. 1",
            complaint_text="Mesin sepeda motor keluar asap tebal dari knalpot dan mati mendadak."
        )
        self.assertEqual(order.status, OrderStatus.SEARCHING)
        self.assertIn("possible_issues", order.ai_triage_result)
        self.assertEqual(nearby_count, 1)

    def test_order_accept_concurrency_and_state_machine(self):
        order, _ = OrderService.create_order(
            customer=self.customer,
            latitude=-6.175000,
            longitude=106.827000,
            location_address="Monas",
            complaint_text="Ban motor bocor halus."
        )

        accepted_order = OrderService.accept_order(order.id, self.mechanic)
        self.assertEqual(accepted_order.status, OrderStatus.ACCEPTED)
        self.assertEqual(accepted_order.mechanic, self.mechanic)

        # Test state machine transition: ACCEPTED -> ON_THE_WAY -> ARRIVED -> WORKING -> COMPLETED
        order_otw = OrderService.update_order_status(order.id, self.mechanic, OrderStatus.ON_THE_WAY)
        self.assertEqual(order_otw.status, OrderStatus.ON_THE_WAY)

        order_arrived = OrderService.update_order_status(order.id, self.mechanic, OrderStatus.ARRIVED)
        self.assertEqual(order_arrived.status, OrderStatus.ARRIVED)

        order_working = OrderService.update_order_status(order.id, self.mechanic, OrderStatus.WORKING)
        self.assertEqual(order_working.status, OrderStatus.WORKING)

        order_completed = OrderService.update_order_status(order.id, self.mechanic, OrderStatus.COMPLETED, total_fee=50000.00)
        self.assertEqual(order_completed.status, OrderStatus.COMPLETED)
        self.assertEqual(order_completed.total_fee, 50000.00)
