"""
Authentication Presentation URLs.
Routes for User Registration, Login, Token Refresh, Profile, and Mechanic Status.
"""
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from apps.authentication.presentation.views import (
    RegisterView,
    LoginView,
    UserProfileView,
    MechanicStatusView
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='auth_register'),
    path('login/', LoginView.as_view(), name='auth_login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='auth_token_refresh'),
    path('me/', UserProfileView.as_view(), name='auth_profile'),
    path('mechanic/status/', MechanicStatusView.as_view(), name='auth_mechanic_status'),
]
