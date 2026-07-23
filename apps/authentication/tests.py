"""
Unit tests for Authentication module.
"""
from django.test import TestCase
from django.contrib.gis.geos import Point
from apps.authentication.data.models import User, UserRole
from apps.authentication.domain.services import AuthService


class AuthenticationTestCase(TestCase):
    """
    Test suite for User Model and AuthService.
    """

    def setUp(self):
        self.customer = AuthService.register_user(
            username="customer_test",
            email="customer@otogrid.com",
            password="Password123!",
            phone_number="08123456789",
            full_name="Customer Test",
            role=UserRole.CUSTOMER
        )
        self.mechanic = AuthService.register_user(
            username="mechanic_test",
            email="mechanic@otogrid.com",
            password="Password123!",
            phone_number="08987654321",
            full_name="Mechanic Budi",
            role=UserRole.MECHANIC
        )

    def test_user_creation(self):
        self.assertEqual(self.customer.role, UserRole.CUSTOMER)
        self.assertEqual(self.mechanic.role, UserRole.MECHANIC)
        self.assertTrue(self.customer.check_password("Password123!"))

    def test_jwt_token_generation(self):
        tokens = AuthService.get_jwt_tokens_for_user(self.customer)
        self.assertIn("access", tokens)
        self.assertIn("refresh", tokens)

    def test_mechanic_status_location_update(self):
        updated_mechanic = AuthService.update_mechanic_status_and_location(
            user=self.mechanic,
            is_online=True,
            latitude=-6.175392,
            longitude=106.827153
        )
        self.assertTrue(updated_mechanic.is_online)
        self.assertIsNotNone(updated_mechanic.current_location)
        self.assertAlmostEqual(updated_mechanic.current_location.y, -6.175392)
        self.assertAlmostEqual(updated_mechanic.current_location.x, 106.827153)
