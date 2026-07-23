"""
Orders Presentation Views.
Provides HTTP API endpoints for Creating Orders, Accepting Orders, State Machine Updates, and Geo Nearby Scans.
"""
from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter

from apps.orders.data.models import Order, OrderStatus
from apps.orders.domain.services.order_service import OrderService
from apps.orders.domain.services.geo_service import GeoMatchingService
from apps.orders.presentation.serializers import (
    OrderCreateSerializer,
    OrderDetailSerializer,
    OrderStatusUpdateSerializer
)


class OrderCreateView(APIView):
    """
    API endpoint for customers to create an emergency mechanic order.
    Triggers AI diagnosis and scans nearby mechanics.
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        request=OrderCreateSerializer,
        responses={201: OrderDetailSerializer}
    )
    def post(self, request):
        if request.user.role != 'CUSTOMER':
            return Response(
                {"detail": "Hanya pelanggan yang dapat membuat pesanan darurat."},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = OrderCreateSerializer(data=request.data)
        if serializer.is_valid():
            order, nearby_count = OrderService.create_order(
                customer=request.user,
                latitude=serializer.validated_data['latitude'],
                longitude=serializer.validated_data['longitude'],
                location_address=serializer.validated_data.get('location_address', ''),
                complaint_text=serializer.validated_data['complaint_text']
            )
            data = OrderDetailSerializer(order).data
            return Response({
                "message": "Pesanan darurat berhasil dibuat. Mencari mekanik terdekat...",
                "nearby_mechanics_count": nearby_count,
                "order": data
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OrderNearbyView(APIView):
    """
    API endpoint for mechanics to list active SEARCHING orders within spatial radius.
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        parameters=[
            OpenApiParameter('radius', type=float, description='Radius pencarian dalam KM (default 5.0 KM)')
        ],
        responses={200: OrderDetailSerializer(many=True)}
    )
    def get(self, request):
        if request.user.role != 'MECHANIC':
            return Response(
                {"detail": "Hanya mitra mekanik yang dapat melihat pesanan di sekitar."},
                status=status.HTTP_403_FORBIDDEN
            )

        if not request.user.current_location:
            return Response(
                {"detail": "Lokasi Anda belum diset. Aktifkan lokasi dan status online terlebih dahulu."},
                status=status.HTTP_400_BAD_REQUEST
            )

        radius_km = float(request.query_params.get('radius', 5.0))
        orders = GeoMatchingService.find_nearby_active_orders(
            mechanic_location=request.user.current_location,
            radius_km=radius_km
        )

        serializer = OrderDetailSerializer(orders, many=True)
        return Response({
            "count": len(orders),
            "orders": serializer.data
        }, status=status.HTTP_200_OK)


class OrderAcceptView(APIView):
    """
    API endpoint for a mechanic to accept an open order (atomic transaction).
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses={200: OrderDetailSerializer})
    def post(self, request, pk: int):
        order = OrderService.accept_order(order_id=pk, mechanic=request.user)
        data = OrderDetailSerializer(order).data
        return Response({
            "message": "Pesanan berhasil diterima. Silakan berangkat menuju lokasi pelanggan.",
            "order": data
        }, status=status.HTTP_200_OK)


class OrderStatusUpdateView(APIView):
    """
    API endpoint to update order status in the State Machine.
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        request=OrderStatusUpdateSerializer,
        responses={200: OrderDetailSerializer}
    )
    def patch(self, request, pk: int):
        serializer = OrderStatusUpdateSerializer(data=request.data)
        if serializer.is_valid():
            order = OrderService.update_order_status(
                order_id=pk,
                user=request.user,
                new_status=serializer.validated_data['status'],
                total_fee=serializer.validated_data.get('total_fee')
            )
            data = OrderDetailSerializer(order).data
            return Response({
                "message": f"Status pesanan berhasil diperbarui menjadi {order.status}.",
                "order": data
            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OrderActiveView(APIView):
    """
    API endpoint to retrieve the active order for the logged-in user.
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses={200: OrderDetailSerializer})
    def get(self, request):
        user = request.user
        active_statuses = [
            OrderStatus.SEARCHING,
            OrderStatus.ACCEPTED,
            OrderStatus.ON_THE_WAY,
            OrderStatus.ARRIVED,
            OrderStatus.WORKING
        ]

        if user.role == 'CUSTOMER':
            active_order = Order.objects.filter(customer=user, status__in=active_statuses).first()
        else:
            active_order = Order.objects.filter(mechanic=user, status__in=active_statuses).first()

        if not active_order:
            return Response({"active_order": None}, status=status.HTTP_200_OK)

        serializer = OrderDetailSerializer(active_order)
        return Response({"active_order": serializer.data}, status=status.HTTP_200_OK)


class OrderDetailView(APIView):
    """
    API endpoint to retrieve details of a specific order by ID.
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses={200: OrderDetailSerializer})
    def get(self, request, pk: int):
        try:
            order = Order.objects.get(pk=pk)
        except Order.DoesNotExist:
            return Response({"detail": "Pesanan tidak ditemukan."}, status=status.HTTP_404_NOT_FOUND)

        if request.user != order.customer and request.user != order.mechanic:
            return Response({"detail": "Akses ditolak."}, status=status.HTTP_403_FORBIDDEN)

        serializer = OrderDetailSerializer(order)
        return Response(serializer.data, status=status.HTTP_200_OK)
