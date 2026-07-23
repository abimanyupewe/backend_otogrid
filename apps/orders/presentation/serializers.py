"""
Orders Presentation Serializers.
Defines serializers for Order Creation, Detailed Retrieval, and Status Updates.
"""
from typing import Dict, Any
from rest_framework import serializers
from apps.authentication.presentation.serializers import UserProfileSerializer
from apps.orders.data.models import Order, OrderStatus


class OrderCreateSerializer(serializers.Serializer):
    """
    Serializer for customer emergency order creation.
    """
    latitude = serializers.FloatField(required=True, min_value=-90.0, max_value=90.0)
    longitude = serializers.FloatField(required=True, min_value=-180.0, max_value=180.0)
    location_address = serializers.CharField(required=False, allow_blank=True, default="")
    complaint_text = serializers.CharField(required=True, min_length=5)


class OrderDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for detailed Order view.
    """
    customer = UserProfileSerializer(read_only=True)
    mechanic = UserProfileSerializer(read_only=True)
    latitude = serializers.SerializerMethodField()
    longitude = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            'id', 'customer', 'mechanic', 'latitude', 'longitude',
            'location_address', 'complaint_text', 'ai_triage_result',
            'status', 'total_fee', 'created_at', 'updated_at'
        ]

    def get_latitude(self, obj: Order) -> float | None:
        if obj.location:
            return obj.location.y
        return None

    def get_longitude(self, obj: Order) -> float | None:
        if obj.location:
            return obj.location.x
        return None


class OrderStatusUpdateSerializer(serializers.Serializer):
    """
    Serializer for updating Order status in the State Machine.
    """
    status = serializers.ChoiceField(choices=OrderStatus.choices, required=True)
    total_fee = serializers.DecimalField(max_digits=12, decimal_places=2, required=False)
