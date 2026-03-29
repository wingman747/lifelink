from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from django.urls import reverse
from django.db.models import Q
from .models import HospitalBloodBankVerification, InstitutionUser
from django.contrib.auth.models import User


@admin.register(HospitalBloodBankVerification)
class InstitutionVerificationAdmin(admin.ModelAdmin):
    list_display = ('name', 'institution_type', 'registration_number', 'email', 'verification_status', 'created_at')
    list_filter = ('is_verified', 'institution_type', 'created_at')
    search_fields = ('name', 'registration_number', 'email', 'phone')
    readonly_fields = ('created_at', 'verified_on')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'institution_type', 'registration_number')
        }),
        ('Contact Details', {
            'fields': ('address', 'phone', 'email')
        }),
        ('Verification Details', {
            'fields': ('is_verified', 'verified_by', 'verified_on', 'reason_for_rejection'),
            'description': 'Check "is_verified" to approve this institution for registration'
        }),
        ('Documents', {
            'fields': ('license_document',),
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )
    
    def verification_status(self, obj):
        if obj.is_verified:
            return format_html('<span style="color: green; font-weight: bold;">✓ Verified</span>')
        return format_html('<span style="color: red; font-weight: bold;">✗ Pending Review</span>')
    verification_status.short_description = 'Verification Status'
    
    def save_model(self, request, obj, form, change):
        # Auto-fill verified_by and verified_on when approving
        if form.cleaned_data.get('is_verified') and not obj.verified_by:
            obj.verified_by = request.user.username
            obj.verified_on = timezone.now()
        # Clear verification details if rejecting
        elif not form.cleaned_data.get('is_verified'):
            obj.verified_by = ''
            obj.verified_on = None
        super().save_model(request, obj, form, change)
    
    actions = ['approve_institutions', 'reject_institutions']
    
    def approve_institutions(self, request, queryset):
        """Bulk approve institutions"""
        count = 0
        for obj in queryset:
            if not obj.is_verified:
                obj.is_verified = True
                obj.verified_by = request.user.username
                obj.verified_on = timezone.now()
                obj.save()
                count += 1
        self.message_user(request, f'{count} institution(s) approved successfully.')
    approve_institutions.short_description = "Approve selected institutions"
    
    def reject_institutions(self, request, queryset):
        """Bulk reject institutions"""
        count = queryset.update(is_verified=False, verified_by='', verified_on=None)
        self.message_user(request, f'{count} institution(s) rejected.')
    reject_institutions.short_description = "Reject selected institutions"


@admin.register(InstitutionUser)
class InstitutionUserAdmin(admin.ModelAdmin):
    list_display = ('get_username', 'get_institution', 'designation', 'activity_status', 'created_at')
    list_filter = ('is_active', 'institution__is_verified', 'created_at')
    search_fields = ('username__username', 'username__email', 'institution__name')
    readonly_fields = ('created_at', 'get_institution_verification_status')
    
    fieldsets = (
        ('User Information', {
            'fields': ('username', 'designation', 'created_at')
        }),
        ('Institution', {
            'fields': ('institution', 'get_institution_verification_status')
        }),
        ('Account Status', {
            'fields': ('is_active',),
            'description': 'Uncheck to deactivate this user account'
        })
    )
    
    def get_username(self, obj):
        return obj.username.username
    get_username.short_description = 'Username'
    
    def get_institution(self, obj):
        return obj.institution.name
    get_institution.short_description = 'Institution'
    
    def activity_status(self, obj):
        if obj.is_active:
            return format_html('<span style="color: green;">🟢 Active</span>')
        return format_html('<span style="color: red;">🔴 Inactive</span>')
    activity_status.short_description = 'Status'
    
    def get_institution_verification_status(self, obj):
        if obj.institution.is_verified:
            return format_html('<span style="color: green;">✓ Verified</span>')
        return format_html('<span style="color: orange;">⚠ Not Verified</span>')
    get_institution_verification_status.short_description = 'Institution Verification Status'
    
    actions = ['deactivate_users', 'activate_users']
    
    def deactivate_users(self, request, queryset):
        count = queryset.update(is_active=False)
        self.message_user(request, f'{count} user(s) deactivated.')
    deactivate_users.short_description = "Deactivate selected users"
    
    def activate_users(self, request, queryset):
        count = queryset.update(is_active=True)
        self.message_user(request, f'{count} user(s) activated.')
    activate_users.short_description = "Activate selected users"