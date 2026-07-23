"""
Orders Admin Configuration.
Registers Order Model in Django Admin.
"""
from django.contrib import admin
from apps.orders.data.models import Order

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'mechanic', 'status', 'total_fee', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('customer__username', 'mechanic__username', 'complaint_text', 'location_address')
    readonly_fields = ('created_at', 'updated_at')
