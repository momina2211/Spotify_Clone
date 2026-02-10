import uuid
from django.utils import timezone

from django.contrib.auth.models import AbstractUser
from django.db import models

# Conditional import to avoid dj-stripe compatibility issues
try:
    from payments.models import SubscriptionPlan
except (ImportError, AttributeError, RuntimeError):
    SubscriptionPlan = None

from users.base_model import UUIDModel
from users.role_enum import RoleEnum

try:
    from djstripe.models import Customer as StripeCustomer
    from djstripe.models import Subscription as StripeSubscription
except (ImportError, AttributeError, RuntimeError):
    StripeCustomer = None
    StripeSubscription = None



class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    role = models.IntegerField(choices=RoleEnum.choices(), default=RoleEnum.USER.value)

    def __str__(self):
        return self.username


class UserProfile(UUIDModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    profile_type = models.IntegerField(choices=RoleEnum.choices(), default=RoleEnum.USER.value)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)

    subscription_plan = models.ForeignKey(
        'payments.SubscriptionPlan',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subscribers'
    )
    stripe_customer = models.OneToOneField(
        'djstripe.Customer',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='user_profile'
    )
    stripe_subscription = models.OneToOneField(
        'djstripe.Subscription',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='user_profile'
    )
    subscription_status = models.CharField(
        max_length=20,
        choices=[
            ('active', 'Active'),
            ('trialing', 'Trialing'),
            ('past_due', 'Past Due'),
            ('canceled', 'Canceled'),
            ('unpaid', 'Unpaid'),
        ],
        default='active'
    )
    subscription_start_date = models.DateTimeField(null=True, blank=True)
    subscription_end_date = models.DateTimeField(null=True, blank=True)
    cancel_at_period_end = models.BooleanField(default=False)
    trial_start = models.DateTimeField(null=True, blank=True)
    trial_end = models.DateTimeField(null=True, blank=True)
    
    # Subscription related fields
    audio_quality = models.CharField(
        max_length=20, 
        choices=[
            ('low', 'Low (96 kbps)'),
            ('medium', 'Medium (160 kbps)'),
            ('high', 'High (320 kbps)'),
        ],
        default='medium'
    )
    is_offline_mode = models.BooleanField(
        default=False,
        help_text="Whether the user can download music for offline listening"
    )
    skip_limit = models.PositiveIntegerField(
        default=6,
        help_text="Number of skips allowed per hour"
    )
    ad_free = models.BooleanField(
        default=False,
        help_text="Whether the user has an ad-free experience"
    )
    
    # Family plan fields
    family_plan_owner = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='family_members'
    )
    family_members_limit = models.PositiveIntegerField(
        default=0,
        help_text="Maximum number of family members allowed (0 for no family plan)"
    )
    
    # Student verification fields
    is_student = models.BooleanField(
        default=False,
        help_text="Whether the user is a verified student"
    )
    student_verification_date = models.DateField(
        null=True,
        blank=True,
        help_text="When the student status was last verified"
    )
    student_school_email = models.EmailField(
        null=True,
        blank=True,
        help_text="School-issued email address for verification"
    )
    student_school_name = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        help_text="Name of the educational institution"
    )
    student_date_of_birth = models.DateField(
        null=True,
        blank=True,
        help_text="Date of birth (must be at least 13 years old)"
    )
    student_enrollment_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date when student enrollment started"
    )
    student_graduation_date = models.DateField(
        null=True,
        blank=True,
        help_text="Expected or actual graduation date"
    )
    is_distance_learning = models.BooleanField(
        default=False,
        help_text="Whether the student is in a distance learning program"
    )
    
    # Duo plan
    duo_partner = models.OneToOneField(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='duo_partner_of'
    )
    
    # Artist bio (enriched from MusicBrainz)
    bio = models.TextField(
        blank=True,
        null=True,
        help_text="Artist biography (enriched from external sources)"
    )

    def __str__(self):
        return f"{self.user.username}'s profile"
        
    @property
    def has_active_subscription(self):
        """Check if the user has an active subscription."""
        if not self.subscription_plan or not self.subscription_status:
            return False

        now = timezone.now()

        # Free plan is always active
        if self.subscription_plan.is_free_plan:
            return True

        # For paid plans, check status and period
        if self.subscription_status in ['active', 'trialing']:
            if self.subscription_end_date and self.subscription_end_date > now:
                return True

        return False

    def update_subscription_features(self):
        """Update user features based on their subscription plan."""
        if not self.subscription_plan or SubscriptionPlan is None:
            return

        features = self.subscription_plan.get_features()

        # Update user features based on subscription
        self.audio_quality = features.get('audio_quality', 'medium')
        self.is_offline_mode = features.get('offline_mode', False)
        self.ad_free = features.get('ad_free', False)

        # Update skip limit (None means unlimited, use large number)
        skip_limit = features.get('skip_limit', 6)
        self.skip_limit = 999999 if skip_limit is None else skip_limit

        # Update family/duo plan settings
        if self.subscription_plan.plan_type == SubscriptionPlan.PlanType.FAMILY:
            self.family_members_limit = 5  # 1 owner + 5 members
        elif self.subscription_plan.plan_type == SubscriptionPlan.PlanType.DUO:
            self.family_members_limit = 1  # 1 owner + 1 member
        else:
            self.family_members_limit = 0

        self.save()
    
    @property
    def is_student_verified(self):
        """Check if student verification is valid (verified and not expired)."""
        if not self.is_student:
            return False
        
        # Student verification expires after 2 years
        if self.student_verification_date:
            from datetime import timedelta
            expiry_date = self.student_verification_date + timedelta(days=730)  # 2 years
            return timezone.now().date() <= expiry_date
        
        return False
    
    @property
    def is_at_least_13(self):
        """Check if user is at least 13 years old."""
        if not self.student_date_of_birth:
            return False
        from datetime import date
        today = date.today()
        age = today.year - self.student_date_of_birth.year - (
            (today.month, today.day) < (self.student_date_of_birth.month, self.student_date_of_birth.day)
        )
        return age >= 13


class StudentVerification(UUIDModel):
    """Model to track student verification requests and documents."""
    
    class VerificationStatus(models.TextChoices):
        PENDING = 'pending', 'Pending Review'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'
        EXPIRED = 'expired', 'Expired'
    
    class VerificationMethod(models.TextChoices):
        EMAIL = 'email', 'School Email Verification'
        DOCUMENT = 'document', 'Document Upload'
    
    class DocumentType(models.TextChoices):
        SCHOOL_ID = 'school_id', 'School ID Card'
        CLASS_SCHEDULE = 'class_schedule', 'Class Schedule'
        TRANSCRIPT = 'transcript', 'Transcript'
        ENROLLMENT_LETTER = 'enrollment_letter', 'Enrollment Verification Letter'
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='student_verifications'
    )
    status = models.CharField(
        max_length=20,
        choices=VerificationStatus.choices,
        default=VerificationStatus.PENDING
    )
    verification_method = models.CharField(
        max_length=20,
        choices=VerificationMethod.choices,
        default=VerificationMethod.EMAIL,
        help_text="Both email and document are required, but this field indicates primary method"
    )
    
    # Email verification fields
    school_email = models.EmailField(
        null=True,
        blank=True,
        help_text="School-issued email address"
    )
    email_verified = models.BooleanField(
        default=False,
        help_text="Whether the school email has been verified"
    )
    
    # Document verification fields
    document_type = models.CharField(
        max_length=30,
        choices=DocumentType.choices,
        null=True,
        blank=True
    )
    document_file = models.ImageField(
        upload_to='student_verification/',
        null=True,
        blank=True,
        help_text="Uploaded verification document"
    )
    
    # Additional information
    school_name = models.CharField(
        max_length=200,
        null=True,
        blank=True
    )
    full_name_on_document = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        help_text="Full name as it appears on the document"
    )
    enrollment_date = models.DateField(
        null=True,
        blank=True
    )
    graduation_date = models.DateField(
        null=True,
        blank=True
    )
    
    # Review information
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_verifications',
        help_text="Admin user who reviewed this verification"
    )
    reviewed_at = models.DateTimeField(
        null=True,
        blank=True
    )
    rejection_reason = models.TextField(
        null=True,
        blank=True,
        help_text="Reason for rejection if verification was rejected"
    )
    notes = models.TextField(
        null=True,
        blank=True,
        help_text="Additional notes from reviewer"
    )
    
    # Metadata
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="IP address from which verification was submitted"
    )
    user_agent = models.TextField(
        null=True,
        blank=True,
        help_text="User agent string from verification submission"
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Student Verification'
        verbose_name_plural = 'Student Verifications'
    
    def __str__(self):
        return f"Student Verification for {self.user.username} - {self.get_status_display()}"
    
    def approve(self, reviewer):
        """Approve the student verification."""
        from django.utils import timezone
        from datetime import date
        
        self.status = self.VerificationStatus.APPROVED
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()
        self.save()
        
        # Update user profile
        profile = self.user.profile
        profile.is_student = True
        profile.student_verification_date = date.today()
        if self.school_email:
            profile.student_school_email = self.school_email
        if self.school_name:
            profile.student_school_name = self.school_name
        if self.enrollment_date:
            profile.student_enrollment_date = self.enrollment_date
        if self.graduation_date:
            profile.student_graduation_date = self.graduation_date
        profile.save()
    
    def reject(self, reviewer, reason=None):
        """Reject the student verification."""
        from django.utils import timezone
        
        self.status = self.VerificationStatus.REJECTED
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()
        if reason:
            self.rejection_reason = reason
        self.save()
        
        # Update user profile
        profile = self.user.profile
        profile.is_student = False
        profile.save()