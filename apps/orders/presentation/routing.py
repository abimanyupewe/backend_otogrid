"""
Orders WebSockets Routing.
Defines WSS URL routing patterns for real-time order consumers.
"""
from django.urls import re_path
from apps.orders.presentation.consumers import OrderConsumer

websocket_urlpatterns = [
    re_path(r'^ws/orders/(?P<order_id>\d+)/$', OrderConsumer.as_asgi()),
]
