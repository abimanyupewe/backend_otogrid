"""
Orders Admin Configuration using Django Unfold (Tailwind CSS UI).
Registers Order Model with native Unfold Actions, Badges, and AI Triage triggers.
"""
from django.contrib import admin
from django.contrib import messages
from django.utils.html import format_html
from unfold.admin import ModelAdmin
from unfold.decorators import action, display
from apps.orders.data.models import Order
from apps.orders.domain.services.ai_service import AITriageService


@admin.register(Order)
class OrderAdmin(ModelAdmin):
    list_display = (
        'id', 
        'customer', 
        'mechanic', 
        'status_badge', 
        'danger_level_badge', 
        'total_fee', 
        'created_at'
    )
    list_filter = ('status', 'created_at')
    search_fields = ('customer__username', 'mechanic__username', 'complaint_text', 'location_address')
    readonly_fields = ('created_at', 'updated_at', 'location', 'ai_triage_result')
    actions = ['run_ai_triage_action']

    @display(description="Status Order", ordering="status")
    def status_badge(self, obj):
        colors = {
            'SEARCHING': 'bg-amber-100 text-amber-800 dark:bg-amber-900/50 dark:text-amber-300',
            'ACCEPTED': 'bg-blue-100 text-blue-800 dark:bg-blue-900/50 dark:text-blue-300',
            'ARRIVED': 'bg-indigo-100 text-indigo-800 dark:bg-indigo-900/50 dark:text-indigo-300',
            'REPAIRING': 'bg-purple-100 text-purple-800 dark:bg-purple-900/50 dark:text-purple-300',
            'COMPLETED': 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/50 dark:text-emerald-300',
            'CANCELLED': 'bg-red-100 text-red-800 dark:bg-red-900/50 dark:text-red-300',
        }
        color = colors.get(obj.status, 'bg-gray-100 text-gray-800')
        return format_html(
            '<span class="px-2.5 py-1 text-xs font-semibold rounded-full {}">{}</span>',
            color, obj.get_status_display()
        )

    @display(description="AI Danger Level")
    def danger_level_badge(self, obj):
        if not obj.ai_triage_result or not isinstance(obj.ai_triage_result, dict):
            return format_html('<span class="text-xs text-gray-400">Belum Didiagnosa</span>')

        level = obj.ai_triage_result.get('danger_level', 'UNKNOWN')
        level_colors = {
            'CRITICAL': 'bg-red-100 text-red-800 dark:bg-red-900/60 dark:text-red-200 font-bold',
            'HIGH': 'bg-amber-100 text-amber-800 dark:bg-amber-900/60 dark:text-amber-200 font-semibold',
            'MEDIUM': 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/60 dark:text-yellow-200',
            'LOW': 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/60 dark:text-emerald-200',
        }
        color = level_colors.get(level, 'bg-gray-100 text-gray-800')
        return format_html(
            '<span class="px-2.5 py-1 text-xs rounded-full {}">🤖 {}</span>',
            color, level
        )

    @action(description="⚡ Jalankan Diagnosa AI Triage Ulang")
    def run_ai_triage_action(self, request, queryset):
        count = 0
        for order in queryset:
            if order.complaint_text:
                result = AITriageService.diagnose_complaint(order.complaint_text)
                order.ai_triage_result = result
                order.save()
                count += 1
        
        self.message_user(
            request, 
            f"Berhasil menjalankan AI Triage untuk {count} pesanan darurat.", 
            messages.SUCCESS
        )
