"""
Custom Admin Dashboard Callbacks for OtoGrid Unfold Admin.
"""
# pyrefly: ignore [missing-import]
from django.contrib import messages
from apps.orders.data.models import Order, OrderStatus
from apps.authentication.data.models import User
from apps.orders.domain.services.ai_service import AITriageService


def dashboard_callback(request, context):
    """
    Native Unfold Dashboard Callback.
    Injects KPI metrics & AI Triage Engine Playground directly onto the main Django Admin home page (/admin/).
    """
    total_orders = Order.objects.count()
    searching_orders = Order.objects.filter(status='SEARCHING').count()
    completed_orders = Order.objects.filter(status='COMPLETED').count()
    total_mechanics = User.objects.filter(role='MECHANIC').count()

    ai_result = None
    complaint_text = ""
    order_created = None

    # Process AI Triage Playground submitted directly from the dashboard home page
    if request.method == "POST":
        complaint_text = request.POST.get("complaint_text", "").strip()

        if "create_order_submit" in request.POST:
            if complaint_text:
                ai_result = AITriageService.diagnose_complaint(complaint_text)
                
                # Get or assign customer (fallback to requesting admin user)
                customer_user = request.user if request.user.is_authenticated else User.objects.first()

                new_order = Order.objects.create(
                    customer=customer_user,
                    complaint_text=complaint_text,
                    ai_triage_result=ai_result,
                    status=OrderStatus.SEARCHING,
                    location_data={'lat': -6.2088, 'lng': 106.8456}, # Default Monas Jakarta
                    location_address="Lokasi Darurat Admin (Pusat Kendali OtoGrid)"
                )
                order_created = new_order
                messages.success(request, f" Order Darurat #{new_order.id} berhasil dibuat dengan status MENCARI MEKANIK!")

        elif complaint_text:
            # Always process AI triage whenever complaint_text is submitted
            ai_result = AITriageService.diagnose_complaint(complaint_text)

    context.update({
        "kpis": [
            {
                "title": "Total Emergency Orders",
                "metric": total_orders,
                "footer": "Keseluruhan permintaan bantuan",
            },
            {
                "title": "Searching Mechanic",
                "metric": searching_orders,
                "footer": "Pesanan aktif mencari mekanik",
            },
            {
                "title": "Repair Completed",
                "metric": completed_orders,
                "footer": "Perbaikan berhasil ditangani",
            },
            {
                "title": "Registered Mechanics",
                "metric": total_mechanics,
                "footer": "Mitra mekanik OtoGrid",
            },
        ],
        "ai_playground": {
            "complaint_text": complaint_text,
            "result": ai_result,
            "order_created": order_created,
        }
    })
    return context
