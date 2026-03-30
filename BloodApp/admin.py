from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from django.urls import reverse
from django.db.models import Q
from django.contrib.auth.models import User
from .models import BloodRequest, BloodRequestNotification, BloodInventory

# ============================================
# BLOOD REQUEST ADMIN
# ============================================

@admin.register(BloodRequest)
class BloodRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'hospital_name', 'blood_bank_name', 'blood_type', 'units_required', 'status_badge', 'urgency_badge', 'created_at')
    list_filter = ('status', 'urgency_level', 'blood_type', 'created_at')
    search_fields = ('hospital__name', 'blood_bank__name', 'blood_type')
    readonly_fields = ('created_at', 'updated_at', 'approved_at', 'fulfilled_at')
    
    fieldsets = (
        ('Request Information', {
            'fields': ('hospital', 'blood_bank', 'blood_type', 'units_required')
        }),
        ('Status & Urgency', {
            'fields': ('status', 'urgency_level')
        }),
        ('Approval Details', {
            'fields': ('approved_by', 'units_approved', 'approved_at', 'remarks')
        }),
        ('Fulfillment Details', {
            'fields': ('units_fulfilled', 'fulfilled_at')
        }),
        ('Rejection Details', {
            'fields': ('rejection_reason',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def hospital_name(self, obj):
        return obj.hospital.name
    hospital_name.short_description = 'Hospital'
    
    def blood_bank_name(self, obj):
        return obj.blood_bank.name
    blood_bank_name.short_description = 'Blood Bank'
    
    def status_badge(self, obj):
        colors = {
            'pending': '#f59e0b',
            'approved': '#3b82f6',
            'fulfilled': '#16a34a',
            'rejected': '#dc2626',
            'cancelled': '#6b7280'
        }
        color = colors.get(obj.status, '#gray')
        return format_html(
            '<span style="background: {}; color: white; padding: 4px 12px; border-radius: 4px; font-weight: 600;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def urgency_badge(self, obj):
        colors = {
            'low': '#3b82f6',
            'medium': '#f59e0b',
            'high': '#dc2626'
        }
        color = colors.get(obj.urgency_level, '#gray')
        icons = {
            'low': 'ℹ️',
            'medium': '⚠️',
            'high': '🚨'
        }
        icon = icons.get(obj.urgency_level, '')
        return format_html(
            '<span style="background: {}; color: white; padding: 4px 12px; border-radius: 4px; font-weight: 600;">{} {}</span>',
            color,
            icon,
            obj.get_urgency_level_display()
        )
    urgency_badge.short_description = 'Urgency'
    
    actions = ['approve_requests', 'fulfill_requests', 'reject_requests']
    
    def approve_requests(self, request, queryset):
        """Bulk approve requests"""
        count = queryset.filter(status='pending').update(
            status='approved',
            approved_by=request.user,
            approved_at=timezone.now()
        )
        self.message_user(request, f'{count} request(s) approved.')
    approve_requests.short_description = "Approve selected requests"
    
    def fulfill_requests(self, request, queryset):
        """Bulk mark as fulfilled"""
        count = queryset.filter(status='approved').update(
            status='fulfilled',
            fulfilled_at=timezone.now()
        )
        self.message_user(request, f'{count} request(s) fulfilled.')
    fulfill_requests.short_description = "Mark as fulfilled"
    
    def reject_requests(self, request, queryset):
        """Bulk reject requests"""
        count = queryset.filter(status='pending').update(status='rejected')
        self.message_user(request, f'{count} request(s) rejected.')
    reject_requests.short_description = "Reject selected requests"


# ============================================
# BLOOD REQUEST NOTIFICATION ADMIN
# ============================================

@admin.register(BloodRequestNotification)
class BloodRequestNotificationAdmin(admin.ModelAdmin):
    list_display = ('request', 'notification_type_badge', 'is_read_badge', 'created_at')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('request__hospital__name', 'message')
    readonly_fields = ('created_at', 'request', 'message')
    
    fieldsets = (
        ('Notification Details', {
            'fields': ('request', 'notification_type', 'message')
        }),
        ('Status', {
            'fields': ('is_read',)
        }),
        ('Timestamp', {
            'fields': ('created_at',)
        })
    )
    
    def notification_type_badge(self, obj):
        colors = {
            'created': '#3b82f6',
            'approved': '#16a34a',
            'fulfilled': '#10b981',
            'rejected': '#dc2626',
            'cancelled': '#6b7280'
        }
        color = colors.get(obj.notification_type, '#gray')
        return format_html(
            '<span style="background: {}; color: white; padding: 4px 12px; border-radius: 4px; font-weight: 600;">{}</span>',
            color,
            obj.get_notification_type_display()
        )
    notification_type_badge.short_description = 'Type'
    
    def is_read_badge(self, obj):
        if obj.is_read:
            return format_html('<span style="color: green;">✓ Read</span>')
        return format_html('<span style="color: orange;">📬 Unread</span>')
    is_read_badge.short_description = 'Read Status'
    
    actions = ['mark_as_read', 'mark_as_unread']
    
    def mark_as_read(self, request, queryset):
        count = queryset.update(is_read=True)
        self.message_user(request, f'{count} notification(s) marked as read.')
    mark_as_read.short_description = "Mark as read"
    
    def mark_as_unread(self, request, queryset):
        count = queryset.update(is_read=False)
        self.message_user(request, f'{count} notification(s) marked as unread.')
    mark_as_unread.short_description = "Mark as unread"


# ============================================
# BLOOD INVENTORY ADMIN
# ============================================

@admin.register(BloodInventory)
class BloodInventoryAdmin(admin.ModelAdmin):
    list_display = ('blood_bank_name', 'total_units', 'o_positive_units', 'a_positive_units', 'b_positive_units', 'ab_positive_units', 'last_updated')
    readonly_fields = ('blood_bank', 'last_updated', 'get_inventory_summary')
    
    fieldsets = (
        ('Blood Bank', {
            'fields': ('blood_bank', 'last_updated')
        }),
        ('Positive Blood Types', {
            'fields': ('O_positive', 'A_positive', 'B_positive', 'AB_positive')
        }),
        ('Negative Blood Types', {
            'fields': ('O_negative', 'A_negative', 'B_negative', 'AB_negative')
        }),
        ('Summary', {
            'fields': ('get_inventory_summary',)
        })
    )
    
    def blood_bank_name(self, obj):
        return obj.blood_bank.name
    blood_bank_name.short_description = 'Blood Bank'
    
    def total_units(self, obj):
        total = (obj.O_positive + obj.O_negative + obj.A_positive + obj.A_negative + 
                obj.B_positive + obj.B_negative + obj.AB_positive + obj.AB_negative)
        return format_html(
            '<span style="background: #dc2626; color: white; padding: 4px 12px; border-radius: 4px; font-weight: 600;">{} Units</span>',
            total
        )
    total_units.short_description = 'Total Units'
    
    def o_positive_units(self, obj):
        return obj.O_positive
    o_positive_units.short_description = 'O+'
    
    def a_positive_units(self, obj):
        return obj.A_positive
    a_positive_units.short_description = 'A+'
    
    def b_positive_units(self, obj):
        return obj.B_positive
    b_positive_units.short_description = 'B+'
    
    def ab_positive_units(self, obj):
        return obj.AB_positive
    ab_positive_units.short_description = 'AB+'
    
    def get_inventory_summary(self, obj):
        inventory = obj.get_inventory_dict()
        html = '<table style="border-collapse: collapse; width: 100%;">'
        html += '<tr style="background: #f5f5f5;">'
        for blood_type in inventory.keys():
            html += f'<th style="border: 1px solid #ddd; padding: 8px; text-align: center; font-weight: 600;">{blood_type}</th>'
        html += '</tr><tr>'
        for blood_type, quantity in inventory.items():
            color = '#16a34a' if quantity > 5 else '#f59e0b' if quantity > 0 else '#dc2626'
            html += f'<td style="border: 1px solid #ddd; padding: 8px; text-align: center; color: {color}; font-weight: 600;">{quantity}</td>'
        html += '</tr></table>'
        return format_html(html)
    get_inventory_summary.short_description = 'Current Inventory Summary'