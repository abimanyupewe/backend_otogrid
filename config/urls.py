"""
URL configuration for OtoGrid project.
Routes endpoints for API v1 (Authentication, Orders), Swagger OpenAPI documentation, and root redirect.
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

urlpatterns = [
    # Root Redirect to Admin Dashboard
    path('', RedirectView.as_view(url='/admin/', permanent=False)),

    # Django Admin Interface
    path('admin/', admin.site.urls),
    
    # API v1 Endpoints
    path('api/v1/auth/', include('apps.authentication.presentation.urls')),
    path('api/v1/orders/', include('apps.orders.presentation.urls')),

    # OpenAPI 3.0 / Swagger Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
