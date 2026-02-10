from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from users.models import UserProfile, User, StudentVerification


@admin.register(StudentVerification)
class StudentVerificationAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'user', 'status', 'verification_method', 'school_email',
        'school_name', 'created_at', 'reviewed_at', 'reviewed_by'
    ]
    list_filter = ['status', 'verification_method', 'created_at', 'reviewed_at']
    search_fields = ['user__username', 'user__email', 'school_email', 'school_name']
    readonly_fields = ['id', 'created_at', 'ip_address', 'user_agent']
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'id', 'created_at')
        }),
        ('Verification Details', {
            'fields': (
                'status', 'verification_method', 'school_email', 'email_verified',
                'document_type', 'document_file', 'full_name_on_document'
            )
        }),
        ('School Information', {
            'fields': (
                'school_name', 'enrollment_date', 'graduation_date',
                'is_distance_learning'
            )
        }),
        ('Review Information', {
            'fields': (
                'reviewed_by', 'reviewed_at', 'rejection_reason', 'notes'
            )
        }),
        ('Metadata', {
            'fields': ('ip_address', 'user_agent'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['approve_verifications', 'reject_verifications']
    
    def approve_verifications(self, request, queryset):
        """Approve selected verifications."""
        count = 0
        for verification in queryset.filter(status=StudentVerification.VerificationStatus.PENDING):
            verification.approve(request.user)
            count += 1
        self.message_user(request, f'{count} verification(s) approved successfully.')
    approve_verifications.short_description = "Approve selected verifications"
    
    def reject_verifications(self, request, queryset):
        """Reject selected verifications."""
        count = 0
        for verification in queryset.filter(status=StudentVerification.VerificationStatus.PENDING):
            verification.reject(request.user, "Bulk rejection by admin")
            count += 1
        self.message_user(request, f'{count} verification(s) rejected.')
    reject_verifications.short_description = "Reject selected verifications"
    
    def get_readonly_fields(self, request, obj=None):
        """Make status readonly if already reviewed."""
        readonly = list(self.readonly_fields)
        if obj and obj.status != StudentVerification.VerificationStatus.PENDING:
            readonly.append('status')
        return readonly


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'subscription_plan', 'subscription_status',
        'is_student', 'student_verification_date'
    ]
    list_filter = ['subscription_status', 'is_student', 'subscription_plan']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['id', 'created_at']


# Register your models here.
admin.site.register(User)