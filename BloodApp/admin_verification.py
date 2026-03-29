from django.contrib import admin
from django.utils.html import format_html
from .models import HospitalBloodBankVerification, InstitutionUser

@admin.register(HospitalBloodBankVerification)
class InstitutionVerificationAdmin(admin.ModelAdmin):
    list_display = ('name', 'institution_type', 'registration_number', 'verification_status', 'created_at')
    list_filter = ('is_verified', 'institution_type', 'created_at')
    search_fields = ('name', 'registration_number', 'email')
    readonly_fields = ('created_at', 'verified_on')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'institution_type', 'registration_number')
        }),
        ('Contact Details', {
            'fields': ('address', 'phone', 'email')
        }),
        ('Verification', {
            'fields': ('is_verified', 'verified_by', 'verified_on', 'reason_for_rejection', 'license_document')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )
    
    def verification_status(self, obj):
        if obj.is_verified:
            return format_html('<span style="color: green;">✓ Verified</span>')
        return format_html('<span style="color: red;">✗ Pending</span>')
    verification_status.short_description = 'Status'
    
    def save_model(self, request, obj, form, change):
        if form.cleaned_data.get('is_verified') and not obj.verified_by:
            obj.verified_by = request.user.username
            obj.verified_on = timezone.now()
        super().save_model(request, obj, form, change)

@admin.register(InstitutionUser)
class InstitutionUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'institution', 'designation', 'is_active')
    list_filter = ('institution', 'is_active')
    search_fields = ('username__username', 'institution__name')