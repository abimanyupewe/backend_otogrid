"""
Authentication Presentation Serializers.
Defines request/response validation schemas for registration, login, profile, and mechanic status.
"""
from typing import Dict, Any
from rest_framework import serializers
from django.contrib.auth import authenticate
from apps.authentication.data.models import User, UserRole


class UserRegisterSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.
    """
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'phone_number', 'full_name', 'role']
        read_only_fields = ['id']

    def validate_email(self, value: str) -> str:
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Email sudah terdaftar.")
        return value.lower()

    def validate_username(self, value: str) -> str:
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError("Username sudah terdaftar.")
        return value


class UserLoginSerializer(serializers.Serializer):
    """
    Serializer for user login credentials.
    """
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        username = attrs.get('username')
        password = attrs.get('password')

        user = authenticate(username=username, password=password)
        if not user:
            # Fallback check by email
            user_obj = User.objects.filter(email__iexact=username).first()
            if user_obj:
                user = authenticate(username=user_obj.username, password=password)

        if not user:
            raise serializers.ValidationError("Kredensial username/password tidak valid.")

        if not user.is_active:
            raise serializers.ValidationError("Akun pengguna ini nonaktif.")

        attrs['user'] = user
        return attrs


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for user profile display and updates.
    """
    latitude = serializers.SerializerMethodField()
    longitude = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'full_name', 'phone_number',
            'role', 'is_online', 'latitude', 'longitude', 'created_at'
        ]
        read_only_fields = ['id', 'username', 'email', 'role', 'created_at']

    def get_latitude(self, obj: User) -> float | None:
        if obj.current_location:
            return obj.current_location.y
        return None

    def get_longitude(self, obj: User) -> float | None:
        if obj.current_location:
            return obj.current_location.x
        return None


class MechanicLocationStatusSerializer(serializers.Serializer):
    """
    Serializer for mechanics updating their online status and location coordinates.
    """
    is_online = serializers.BooleanField(required=False)
    latitude = serializers.FloatField(required=False, min_value=-90.0, max_value=90.0)
    longitude = serializers.FloatField(required=False, min_value=-180.0, max_value=180.0)

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        lat = attrs.get('latitude')
        lng = attrs.get('longitude')
        if (lat is not None and lng is None) or (lng is not None and lat is None):
            raise serializers.ValidationError("Latitude dan Longitude harus dikirimkan bersamaan.")
        return attrs
