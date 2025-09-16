import uuid
from datetime import timezone

from django.contrib.auth.models import AbstractUser
from django.db import models

from payments.models import SubscriptionPlan
from users.base_model import UUIDModel
from users.role_enum import RoleEnum
from djstripe.models import Customer as StripeCustomer
from djstripe.models import Subscription as StripeSubscription



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
        SubscriptionPlan,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subscribers'
    )
    stripe_customer = models.OneToOneField(
        StripeCustomer,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='user_profile'
    )
    stripe_subscription = models.OneToOneField(
        StripeSubscription,
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
    
    # Student verification
    is_student = models.BooleanField(
        default=False,
        help_text="Whether the user is a verified student"
    )
    student_verification_date = models.DateField(
        null=True,
        blank=True,
        help_text="When the student status was last verified"
    )
    
    # Duo plan
    duo_partner = models.OneToOneField(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='duo_partner_of'
    )

    def __str__(self):
        return f"{self.user.username}'s profile"
        
    def update_subscription_features(self, plan_name):
        """Update user features based on their subscription plan."""
        if plan_name == 'free':
            self.audio_quality = 'medium'
            self.is_offline_mode = False
            self.skip_limit = 6
            self.ad_free = False
            self.family_plan_owner = None
            self.family_members_limit = 0
            self.duo_partner = None
        elif plan_name == 'individual':
            self.audio_quality = 'high'
            self.is_offline_mode = True
            self.skip_limit = float('inf')
            self.ad_free = True
            self.family_plan_owner = None
            self.family_members_limit = 0
            self.duo_partner = None
        elif plan_name == 'duo':
            self.audio_quality = 'high'
            self.is_offline_mode = True
            self.skip_limit = float('inf')
            self.ad_free = True
            self.family_plan_owner = None
            self.family_members_limit = 0
            # Note: duo_partner should be set separately
        elif plan_name == 'family':
            self.audio_quality = 'high'
            self.is_offline_mode = True
            self.skip_limit = float('inf')
            self.ad_free = True
            self.family_members_limit = 5  # 1 owner + 5 members = 6 total
            self.duo_partner = None
        elif plan_name == 'student':
            self.audio_quality = 'high'
            self.is_offline_mode = True
            self.skip_limit = float('inf')
            self.ad_free = True
            self.family_plan_owner = None
            self.family_members_limit = 0
            self.duo_partner = None
            self.is_student = True
            
        self.save()


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
    if not self.subscription_plan:
        return

    features = self.subscription_plan.get_features()

    # Update user features based on subscription
    self.audio_quality = features.get('audio_quality', 'medium')
    self.is_offline_mode = features.get('offline_mode', False)
    self.ad_free = features.get('ad_free', False)

    # Update skip limit (None means unlimited)
    self.skip_limit = features.get('skip_limit', 6) or float('inf')

    # Update family/duo plan settings
    if self.subscription_plan.plan_type == SubscriptionPlan.PlanType.FAMILY:
        self.family_members_limit = 5  # 1 owner + 5 members
    elif self.subscription_plan.plan_type == SubscriptionPlan.PlanType.DUO:
        self.family_members_limit = 1  # 1 owner + 1 member
    else:
        self.family_members_limit = 0

    self.save()