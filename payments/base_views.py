# payments/base_views.py
"""
Base class for Stripe-related view operations.
Contains common methods to reduce code redundancy.
"""
from django.conf import settings
from rest_framework.response import Response
from rest_framework import status
import stripe


class StripeBaseMixin:
    """Base mixin class for Stripe operations."""
    
    @staticmethod
    def check_stripe_configuration():
        """Check if Stripe is properly configured."""
        if not settings.STRIPE_SECRET_KEY:
            return Response(
                {'error': 'Stripe is not configured. Please set STRIPE_SECRET_KEY in your environment variables.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        return None
    
    @staticmethod
    def get_or_create_stripe_customer(user, profile):
        """
        Get existing Stripe customer ID or create a new one.
        
        Args:
            user: Django User instance
            profile: UserProfile instance
            
        Returns:
            str: Stripe customer ID
        """
        if profile.stripe_customer:
            stripe_customer_id = (
                profile.stripe_customer.id 
                if hasattr(profile.stripe_customer, 'id') 
                else str(profile.stripe_customer)
            )
        else:
            # Create Stripe customer
            customer = stripe.Customer.create(
                email=user.email,
                name=user.get_full_name() or user.username,
                metadata={
                    'user_id': str(user.id),
                    'username': user.username
                }
            )
            stripe_customer_id = customer.id
            # Note: Customer will be saved in webhook handler
        
        return stripe_customer_id
    
    @staticmethod
    def get_stripe_subscription_id(profile):
        """
        Extract Stripe subscription ID from profile.
        
        Args:
            profile: UserProfile instance
            
        Returns:
            str or None: Stripe subscription ID
        """
        if profile.stripe_subscription:
            return (
                profile.stripe_subscription.id 
                if hasattr(profile.stripe_subscription, 'id') 
                else str(profile.stripe_subscription)
            )
        # Fallback: try to get from string field if it exists
        return getattr(profile, 'stripe_subscription_id', None)
    
    @staticmethod
    def get_stripe_price_id(plan, create_if_missing=True):
        """
        Get Stripe price ID for a subscription plan.
        
        Args:
            plan: SubscriptionPlan instance
            create_if_missing: If True, create Stripe price if it doesn't exist
            
        Returns:
            str: Stripe price ID
            
        Raises:
            Exception: If price cannot be retrieved or created
        """
        if plan.stripe_price_id_string:
            return plan.stripe_price_id_string
        elif plan.stripe_price:
            return (
                plan.stripe_price.id 
                if hasattr(plan.stripe_price, 'id') 
                else str(plan.stripe_price)
            )
        elif create_if_missing:
            # This will be handled by the calling method
            return None
        else:
            raise ValueError(f"No Stripe price ID found for plan {plan.id} and create_if_missing is False")
    
    @staticmethod
    def build_checkout_urls(frontend_url=None):
        """
        Build success and cancel URLs for Stripe checkout.
        
        Args:
            frontend_url: Base URL for frontend (defaults to localhost:5173)
            
        Returns:
            tuple: (success_url, cancel_url)
        """
        if not frontend_url:
            frontend_url = 'http://localhost:5173'
        
        success_url = f"{frontend_url}/subscriptions/success?session_id={{CHECKOUT_SESSION_ID}}"
        cancel_url = f"{frontend_url}/subscriptions"
        
        return success_url, cancel_url
    
    @staticmethod
    def get_or_create_user_profile(user):
        """
        Get or create user profile.
        
        Args:
            user: Django User instance
            
        Returns:
            UserProfile: User profile instance
        """
        if not hasattr(user, 'profile'):
            from users.models import UserProfile
            return UserProfile.objects.create(user=user)
        return user.profile
    
    @staticmethod
    def handle_stripe_error(error, default_message="An error occurred with Stripe"):
        """
        Handle Stripe errors and return appropriate response.
        
        Args:
            error: Stripe error exception
            default_message: Default error message if user_message is not available
            
        Returns:
            Response: Error response
        """
        error_message = (
            str(error.user_message) 
            if hasattr(error, 'user_message') and error.user_message 
            else str(error) if str(error) else default_message
        )
        return Response(
            {'error': error_message},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @staticmethod
    def handle_generic_error(error, default_message="An error occurred"):
        """
        Handle generic errors and return appropriate response.
        
        Args:
            error: Exception instance
            default_message: Default error message
            
        Returns:
            Response: Error response
        """
        return Response(
            {'error': str(error) if str(error) else default_message},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @staticmethod
    def check_student_verification(profile, plan):
        """
        Check if student verification is required and valid.
        
        Args:
            profile: UserProfile instance
            plan: SubscriptionPlan instance
            
        Returns:
            Response or None: Error response if verification is required but missing, None otherwise
        """
        from payments.models import SubscriptionPlan
        from users.models import StudentVerification
        
        if plan.plan_type != SubscriptionPlan.PlanType.STUDENT:
            return None
        
        if profile.is_student_verified:
            return None
        
        # Check if there's a pending verification
        pending_verification = StudentVerification.objects.filter(
            user=profile.user,
            status=StudentVerification.VerificationStatus.PENDING
        ).exists()
        
        if pending_verification:
            return Response(
                {
                    'error': 'Student verification is required for Premium Student plan. Your verification request is pending review. Please wait for approval before subscribing.',
                    'requires_verification': True,
                    'verification_status': 'pending'
                },
                status=status.HTTP_403_FORBIDDEN
            )
        else:
            return Response(
                {
                    'error': 'Student verification is required for Premium Student plan. Please submit your student verification first.',
                    'requires_verification': True,
                    'verification_status': 'not_submitted'
                },
                status=status.HTTP_403_FORBIDDEN
            )
