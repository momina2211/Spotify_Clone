
import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from djstripe.models import Price as StripePrice

from users.base_model import UUIDModel


class SubscriptionPlan(UUIDModel):
    """Model representing different subscription plans."""

    class PlanType(models.TextChoices):
        FREE = 'free', _('Free')
        INDIVIDUAL = 'individual', _('Premium Individual')
        DUO = 'duo', _('Premium Duo')
        FAMILY = 'family', _('Premium Family')
        STUDENT = 'student', _('Premium Student')

    name = models.CharField(_('plan name'), max_length=100)
    plan_type = models.CharField(
        _('plan type'),
        max_length=20,
        choices=PlanType.choices,
        unique=True
    )
    stripe_price = models.ForeignKey(
        StripePrice,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text=_('The associated Stripe Price object')
    )
    price = models.DecimalField(
        _('price'),
        max_digits=10,
        decimal_places=2,
        default=0.00
    )
    currency = models.CharField(
        _('currency'),
        max_length=3,
        default='USD'
    )
    billing_cycle = models.CharField(
        _('billing cycle'),
        max_length=20,
        choices=[
            ('monthly', _('Monthly')),
            ('annual', _('Annual'))
        ],
        default='monthly'
    )
    max_members = models.PositiveIntegerField(
        _('maximum members'),
        default=1,
        help_text=_('Maximum number of members allowed (for family/duo plans)')
    )
    features = models.JSONField(
        _('features'),
        default=dict,
        help_text=_('Dictionary of features included in this plan')
    )
    is_active = models.BooleanField(
        _('is active'),
        default=True,
        help_text=_('Whether this plan is currently available for subscription')
    )
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('subscription plan')
        verbose_name_plural = _('subscription plans')
        ordering = ['price']

    def __str__(self):
        return f"{self.get_plan_type_display()} - {self.price} {self.currency}/{self.billing_cycle}"

    @property
    def is_free_plan(self):
        """Check if this is the free plan."""
        return self.plan_type == self.PlanType.FREE

    def get_features(self):
        """Get the features for this plan."""
        default_features = {
            'ad_free': False,
            'offline_mode': False,
            'audio_quality': 'medium',
            'skip_limit': 6,
            'max_playlists': 100,
            'max_devices': 3,
        }

        if self.plan_type == self.PlanType.FREE:
            return {
                **default_features,
                'ad_free': False,
                'offline_mode': False,
                'audio_quality': 'medium',
                'skip_limit': 6,
            }
        elif self.plan_type == self.PlanType.INDIVIDUAL:
            return {
                **default_features,
                'ad_free': True,
                'offline_mode': True,
                'audio_quality': 'high',
                'skip_limit': float('inf'),
            }
        elif self.plan_type == self.PlanType.DUO:
            return {
                **default_features,
                'ad_free': True,
                'offline_mode': True,
                'audio_quality': 'high',
                'skip_limit': float('inf'),
                'max_members': 2,
            }
        elif self.plan_type == self.PlanType.FAMILY:
            return {
                **default_features,
                'ad_free': True,
                'offline_mode': True,
                'audio_quality': 'high',
                'skip_limit': float('inf'),
                'max_members': 6,
                'parental_controls': True,
            }
        elif self.plan_type == self.PlanType.STUDENT:
            return {
                **default_features,
                'ad_free': True,
                'offline_mode': True,
                'audio_quality': 'high',
                'skip_limit': float('inf'),
                'student_discount': True,
            }
        return default_features