"""
Orders Presentation URLs.
Routes for Order Creation, Nearby Scanning, Order Acceptance, State Machine Updates, Active Order, and Order Detail.
"""
from django.urls import path
from apps.orders.presentation.views import (
    OrderCreateView,
    OrderNearbyView,
    OrderAcceptView,
    OrderStatusUpdateView,
    OrderActiveView,
    OrderDetailView
)

urlpatterns = [
    path('create/', OrderCreateView.as_view(), name='order_create'),
    path('nearby/', OrderNearbyView.as_view(), name='order_nearby'),
    path('<int:pk>/accept/', OrderAcceptView.as_view(), name='order_accept'),
    path('<int:pk>/status/', OrderStatusUpdateView.as_view(), name='order_status_update'),
    path('active/', OrderActiveView.as_view(), name='order_active'),
    path('<int:pk>/', OrderDetailView.as_view(), name='order_detail'),
]
