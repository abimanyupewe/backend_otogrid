"""
Authentication Admin Configuration using Django Unfold (Tailwind CSS UI).
Registers Custom User Model in Django Admin.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from unfold.admin import ModelAdmin
from apps.authentication.data.models import User


@admin.register(User)
class CustomUserAdmin(BaseUserAdmin, ModelAdmin):
    list_display = ('username', 'email', 'full_name', 'phone_number', 'role', 'is_online', 'is_staff')
    list_filter = ('role', 'is_online', 'is_staff', 'is_superuser')
    readonly_fields = ('current_location',)
    fieldsets = BaseUserAdmin.fieldsets + (
        ('OtoGrid Extra Fields', {'fields': ('role', 'phone_number', 'full_name', 'is_online', 'current_location')}),
    )
