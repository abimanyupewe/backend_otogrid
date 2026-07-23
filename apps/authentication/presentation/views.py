"""
Authentication Presentation Views.
Provides HTTP API endpoints for User Registration, Login, Profile Management, and Mechanic Status Updates.
"""
from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiResponse

from apps.authentication.domain.services import AuthService
from apps.authentication.presentation.serializers import (
    UserRegisterSerializer,
    UserLoginSerializer,
    UserProfileSerializer,
    MechanicLocationStatusSerializer
)


class RegisterView(APIView):
    """
    API endpoint to register a new Customer or Mechanic user.
    """
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        request=UserRegisterSerializer,
        responses={
            201: OpenApiResponse(description="User registered successfully."),
            400: OpenApiResponse(description="Validation error.")
        }
    )
    def post(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        serializer.is_validate_or_error = True
        if serializer.is_valid():
            user = AuthService.register_user(
                username=serializer.validated_data['username'],
                email=serializer.validated_data['email'],
                password=serializer.validated_data['password'],
                phone_number=serializer.validated_data.get('phone_number'),
                full_name=serializer.validated_data.get('full_name', ''),
                role=serializer.validated_data.get('role', 'CUSTOMER')
            )
            tokens = AuthService.get_jwt_tokens_for_user(user)
            profile_data = UserProfileSerializer(user).data
            return Response({
                "message": "Registrasi pengguna berhasil.",
                "user": profile_data,
                "tokens": tokens
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    """
    API endpoint to authenticate user and receive JWT tokens.
    """
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        request=UserLoginSerializer,
        responses={
            200: OpenApiResponse(description="Authentication successful."),
            400: OpenApiResponse(description="Invalid credentials.")
        }
    )
    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            tokens = AuthService.get_jwt_tokens_for_user(user)
            profile_data = UserProfileSerializer(user).data
            return Response({
                "message": "Login berhasil.",
                "user": profile_data,
                "tokens": tokens
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserProfileView(APIView):
    """
    API endpoint to retrieve and update the logged-in user's profile.
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses={200: UserProfileSerializer})
    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(request=UserProfileSerializer, responses={200: UserProfileSerializer})
    def patch(self, request):
        serializer = UserProfileSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "message": "Profil berhasil diperbarui.",
                "user": serializer.data
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MechanicStatusView(APIView):
    """
    API endpoint for Mechanics to update their online status and location coordinates.
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        request=MechanicLocationStatusSerializer,
        responses={200: OpenApiResponse(description="Mechanic status/location updated successfully.")}
    )
    def post(self, request):
        if request.user.role != 'MECHANIC':
            return Response({
                "detail": "Akses ditolak. Fitur ini hanya untuk mitra mekanik."
            }, status=status.HTTP_403_FORBIDDEN)

        serializer = MechanicLocationStatusSerializer(data=request.data)
        if serializer.is_valid():
            updated_user = AuthService.update_mechanic_status_and_location(
                user=request.user,
                is_online=serializer.validated_data.get('is_online'),
                latitude=serializer.validated_data.get('latitude'),
                longitude=serializer.validated_data.get('longitude')
            )
            return Response({
                "message": "Status dan lokasi mekanik berhasil diperbarui.",
                "is_online": updated_user.is_online,
                "latitude": updated_user.current_location.y if updated_user.current_location else None,
                "longitude": updated_user.current_location.x if updated_user.current_location else None,
            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
