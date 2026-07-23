"""
Authentication Domain Service.
Contains business logic for user registration, authentication, token generation, and mechanic status/location updates.
"""
from typing import Dict, Any, Tuple, Optional
from django.contrib.auth import authenticate
from django.contrib.gis.geos import Point
from rest_framework_simplejwt.tokens import RefreshToken
from apps.authentication.data.models import User, UserRole


class AuthService:
    """
    Service class handling authentication business logic.
    """

    @staticmethod
    def register_user(
        username: str,
        email: str,
        password: str,
        phone_number: Optional[str] = None,
        full_name: str = "",
        role: str = UserRole.CUSTOMER
    ) -> User:
        """
        Registers a new user (Customer or Mechanic).

        Args:
            username (str): Unique username.
            email (str): Unique email address.
            password (str): Account password.
            phone_number (Optional[str]): Contact phone number.
            full_name (str): Full display name.
            role (str): Role choice (CUSTOMER or MECHANIC).

        Returns:
            User: Created User instance.
        """
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            phone_number=phone_number,
            full_name=full_name,
            role=role
        )
        return user

    @staticmethod
    def get_jwt_tokens_for_user(user: User) -> Dict[str, str]:
        """
        Generates JWT access and refresh tokens with custom claims.

        Args:
            user (User): Target user object.

        Returns:
            Dict[str, str]: Dictionary containing 'access' and 'refresh' tokens.
        """
        refresh = RefreshToken.for_user(user)
        # Custom Claims
        refresh['role'] = user.role
        refresh['username'] = user.username
        refresh['full_name'] = user.full_name
        refresh['email'] = user.email

        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }

    @staticmethod
    def update_mechanic_status_and_location(
        user: User,
        is_online: Optional[bool] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None
    ) -> User:
        """
        Updates mechanic online status and spatial PointField location.

        Args:
            user (User): Target mechanic user.
            is_online (Optional[bool]): Online availability flag.
            latitude (Optional[float]): GPS Latitude.
            longitude (Optional[float]): GPS Longitude.

        Returns:
            User: Updated User object.
        """
        if is_online is not None:
            user.is_online = is_online

        if latitude is not None and longitude is not None:
            # Spatial Point in PostGIS: Point(longitude, latitude) srid=4326
            user.current_location = Point(longitude, latitude, srid=4326)

        user.save()
        return user
