# payments/views.py
from datetime import timedelta
from django.utils import timezone

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.authentication import TokenAuthentication
from django.conf import settings
import stripe
from .models import SubscriptionPlan
from .serializers import SubscriptionPlanSerializer, SubscribeSerializer
from .base_views import StripeBaseMixin

# Initialize Stripe API key
stripe.api_key = settings.STRIPE_SECRET_KEY


class SubscriptionViewSet(StripeBaseMixin, viewsets.ViewSet):
    authentication_classes = [TokenAuthentication]
    
    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        # All actions require authentication except list (which allows viewing plans)
        if self.action == 'list':
            permission_classes = [AllowAny]  # Allow viewing plans without auth
        else:
            permission_classes = [IsAuthenticated]  # All other actions require auth
        return [permission() for permission in permission_classes]

    def list(self, request):
        """List all available subscription plans."""
        plans = SubscriptionPlan.objects.filter(is_active=True).order_by('price')
        serializer = SubscriptionPlanSerializer(plans, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def subscribe(self, request):
        """Create a Stripe Checkout Session for subscription or upgrade/downgrade existing subscription."""
        # Check if Stripe is configured
        config_check = self.check_stripe_configuration()
        if config_check:
            return config_check
        
        serializer = SubscribeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        plan = serializer.validated_data['plan_id']
        user = request.user
        
        # Get or create user profile
        profile = self.get_or_create_user_profile(user)

        # Check student verification for student plans
        verification_check = self.check_student_verification(profile, plan)
        if verification_check:
            return verification_check

        try:
            # Check if user has an active subscription and is switching plans
            has_active_subscription = (
                profile.subscription_plan and 
                not profile.subscription_plan.is_free_plan and
                profile.subscription_status in ['active', 'trialing'] and
                profile.subscription_plan.id != plan.id
            )

            # If user has active subscription and switching plans, handle upgrade/downgrade
            if has_active_subscription:
                # Check if we have a Stripe subscription to modify
                stripe_subscription_id = self.get_stripe_subscription_id(profile)
                if stripe_subscription_id:
                    switch_result = self._handle_subscription_switch(profile, plan, request)
                    if switch_result:
                        return switch_result
                # If switch failed or no Stripe subscription, continue with new subscription creation
                # This ensures users can still subscribe even if Stripe subscription is missing

            # Get Stripe price ID (create if missing)
            stripe_price_id = self.get_stripe_price_id(plan, create_if_missing=True)
            if not stripe_price_id:
                stripe_price_id = self._create_stripe_price(plan)

            # Create or get Stripe customer
            stripe_customer_id = self.get_or_create_stripe_customer(user, profile)

            # Determine trial period
            # Note: If trial is set in Stripe Dashboard (price settings), Stripe handles it automatically
            # We only need to set trial_period_days if it's not already configured in Stripe
            trial_period_days = None
            try:
                # Retrieve the Stripe price to check configuration
                stripe_price_obj = stripe.Price.retrieve(stripe_price_id)
                
                # Check if user is eligible for trial (Individual and Student plans)
                if plan.plan_type in [SubscriptionPlan.PlanType.INDIVIDUAL, SubscriptionPlan.PlanType.STUDENT]:
                    # Only set trial if user hasn't used one before
                    if not profile.trial_start:
                        # If trial is not configured in Stripe price, set it here
                        # If it IS configured in Stripe, we don't need to set it (Stripe handles it)
                        trial_period_days = 30
            except stripe.error.StripeError as e:
                # If we can't retrieve the price, fall back to default trial logic
                if plan.plan_type in [SubscriptionPlan.PlanType.INDIVIDUAL, SubscriptionPlan.PlanType.STUDENT]:
                    if not profile.trial_start:
                        trial_period_days = 30

            # Build success and cancel URLs
            frontend_url = request.data.get('frontend_url', 'http://localhost:5173')
            success_url = f"{frontend_url}/subscriptions/success?session_id={{CHECKOUT_SESSION_ID}}"
            cancel_url = f"{frontend_url}/subscriptions"

            # Prepare subscription data
            subscription_data = {
                'metadata': {
                    'user_id': str(user.id),
                    'plan_id': str(plan.id),
                    'plan_type': plan.plan_type,
                }
            }

            # Add trial period if applicable
            # IMPORTANT: When trial_period_days is set, Stripe will NOT charge immediately
            # The payment method is saved but no charge occurs until after the trial ends
            if trial_period_days:
                subscription_data['trial_period_days'] = trial_period_days
                # Ensure no immediate payment - trial means first charge happens after trial ends
                subscription_data['trial_settings'] = {
                    'end_behavior': {
                        'missing_payment_method': 'cancel'  # Cancel if payment method fails after trial
                    }
                }

            # Create Stripe Checkout Session
            # Note: Stripe will collect payment method but NOT charge during trial period
            checkout_session = stripe.checkout.Session.create(
                customer=stripe_customer_id,
                payment_method_types=['card'],
                line_items=[{
                    'price': stripe_price_id,
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={
                    'user_id': str(user.id),
                    'plan_id': str(plan.id),
                    'plan_type': plan.plan_type,
                },
                subscription_data=subscription_data,
                allow_promotion_codes=True,
                # Payment collection: 'always' means collect payment method even during trial
                # But no actual charge happens until trial ends
                payment_method_collection='always',
            )

            return Response({
                'checkout_url': checkout_session.url,
                'session_id': checkout_session.id,
                'status': 'checkout_created'
            })

        except stripe.error.StripeError as e:
            return self.handle_stripe_error(e)
        except Exception as e:
            return self.handle_generic_error(e)

    def _handle_subscription_switch(self, profile, new_plan, request):
        """Handle switching from one subscription plan to another."""
        try:
            # Get Stripe subscription ID
            stripe_subscription_id = self.get_stripe_subscription_id(profile)
            if not stripe_subscription_id:
                # If no Stripe subscription exists, cannot switch - return error
                return Response(
                    {'error': 'No active Stripe subscription found. Please create a new subscription instead.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Retrieve current Stripe subscription
            stripe_subscription = stripe.Subscription.retrieve(stripe_subscription_id)
            
            # Get the new price ID (create if missing)
            new_stripe_price_id = self.get_stripe_price_id(new_plan, create_if_missing=True)
            if not new_stripe_price_id:
                new_stripe_price_id = self._create_stripe_price(new_plan)

            # Update subscription item to new price
            subscription_item_id = stripe_subscription['items']['data'][0]['id']
            
            # Update the subscription
            updated_subscription = stripe.Subscription.modify(
                stripe_subscription_id,
                items=[{
                    'id': subscription_item_id,
                    'price': new_stripe_price_id,
                }],
                proration_behavior='always_invoice',  # Prorate the difference
                metadata={
                    'user_id': str(profile.user.id),
                    'plan_id': str(new_plan.id),
                    'plan_type': new_plan.plan_type,
                }
            )

            # Update profile immediately (webhook will also update it)
            profile.subscription_plan = new_plan
            profile.subscription_status = updated_subscription.get('status', 'active')
            profile.cancel_at_period_end = False  # Reset cancellation if switching plans
            profile.save()
            profile.update_subscription_features()

            return Response({
                'status': 'subscription_updated',
                'message': f'Successfully switched to {new_plan.name}',
                'subscription': SubscriptionPlanSerializer(new_plan).data,
            })

        except stripe.error.StripeError as e:
            return self.handle_stripe_error(e)
        except Exception as e:
            return self.handle_generic_error(e)


    def _get_stripe_interval(self, billing_cycle):
        """Convert billing cycle to Stripe interval format.
        
        Stripe requires: 'day', 'week', 'month', or 'year'
        Our model uses: 'monthly' or 'annual'
        """
        mapping = {
            'monthly': 'month',
            'annual': 'year',
        }
        return mapping.get(billing_cycle, 'month')  # Default to 'month' if unknown

    def _create_stripe_price(self, plan):
        """Create a Stripe Price for a subscription plan if it doesn't exist."""
        try:
            # Convert price to cents
            price_in_cents = int(float(plan.price) * 100)
            
            # Create Stripe Product if needed
            product = stripe.Product.create(
                name=plan.name,
                description=f"Spotify Premium - {plan.name}",
                metadata={
                    'plan_id': str(plan.id),
                    'plan_type': plan.plan_type,
                }
            )

            # Convert billing_cycle to Stripe interval format
            stripe_interval = self._get_stripe_interval(plan.billing_cycle)

            # Create Stripe Price
            price = stripe.Price.create(
                product=product.id,
                unit_amount=price_in_cents,
                currency=plan.currency.lower(),
                recurring={
                    'interval': stripe_interval,  # Must be 'month' or 'year' (not 'monthly' or 'annual')
                },
                metadata={
                    'plan_id': str(plan.id),
                    'plan_type': plan.plan_type,
                }
            )

            # Save Stripe price ID to plan
            plan.stripe_price_id_string = price.id
            plan.save()

            return price.id

        except Exception as e:
            raise Exception(f"Failed to create Stripe price: {str(e)}")

    @action(detail=False, methods=['post'])
    def cancel(self, request):
        """Cancel the current subscription."""
        user = request.user
        profile = user.profile

        if not profile.subscription_plan or profile.subscription_plan.is_free_plan:
            return Response(
                {'error': 'No active subscription found'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Cancel Stripe subscription if exists
            stripe_subscription_id = self.get_stripe_subscription_id(profile)
            if stripe_subscription_id:
                stripe.Subscription.modify(
                    stripe_subscription_id,
                    cancel_at_period_end=True
                )

            # Update user profile
            profile.cancel_at_period_end = True
            profile.save()

            return Response({
                'status': 'subscription_will_cancel',
                'message': 'Subscription will be canceled at the end of the billing period.'
            })

        except stripe.error.StripeError as e:
            return self.handle_stripe_error(e)
        except Exception as e:
            return self.handle_generic_error(e)

    @action(detail=False, methods=['post'])
    def resume(self, request):
        """Resume a canceled subscription that hasn't expired yet."""
        user = request.user
        profile = user.profile

        if not profile.subscription_plan or profile.subscription_plan.is_free_plan:
            return Response(
                {'error': 'No subscription found'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not profile.cancel_at_period_end:
            return Response(
                {'error': 'Subscription is not scheduled for cancellation'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Resume Stripe subscription if exists
            stripe_subscription_id = self.get_stripe_subscription_id(profile)
            if stripe_subscription_id:
                stripe.Subscription.modify(
                    stripe_subscription_id,
                    cancel_at_period_end=False
                )

            # Update user profile
            profile.cancel_at_period_end = False
            profile.save()

            return Response({
                'status': 'subscription_resumed',
                'message': 'Subscription has been resumed successfully.'
            })

        except stripe.error.StripeError as e:
            return self.handle_stripe_error(e)
        except Exception as e:
            return self.handle_generic_error(e)

    @action(detail=False, methods=['post'])
    def one_time_payment(self, request):
        """Create a one-time payment checkout session (for annual or one-time purchases)."""
        # Check if Stripe is configured
        config_check = self.check_stripe_configuration()
        if config_check:
            return config_check
        
        serializer = SubscribeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        plan = serializer.validated_data['plan_id']
        user = request.user
        
        # Get or create user profile
        profile = self.get_or_create_user_profile(user)

        try:
            # For one-time payment, we'll create a payment intent or checkout session
            # Calculate annual price if monthly, or use plan price
            if plan.billing_cycle == 'monthly':
                # Convert monthly to annual (12 months)
                one_time_amount = float(plan.price) * 12
            else:
                one_time_amount = float(plan.price)

            # Get or create Stripe customer
            stripe_customer_id = self.get_or_create_stripe_customer(user, profile)

            # Build success and cancel URLs
            frontend_url = request.data.get('frontend_url', 'http://localhost:5173')
            success_url, cancel_url = self.build_checkout_urls(frontend_url)

            # Create one-time payment checkout session
            checkout_session = stripe.checkout.Session.create(
                customer=stripe_customer_id,
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': plan.currency.lower(),
                        'product_data': {
                            'name': f"{plan.name} - One-time Payment",
                            'description': f"One-time payment for {plan.name}",
                        },
                        'unit_amount': int(one_time_amount * 100),  # Convert to cents
                    },
                    'quantity': 1,
                }],
                mode='payment',  # One-time payment
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={
                    'user_id': str(user.id),
                    'plan_id': str(plan.id),
                    'plan_type': plan.plan_type,
                    'payment_type': 'one_time',
                },
            )

            return Response({
                'checkout_url': checkout_session.url,
                'session_id': checkout_session.id,
                'status': 'checkout_created',
                'amount': one_time_amount,
            })

        except stripe.error.StripeError as e:
            return self.handle_stripe_error(e)
        except Exception as e:
            return self.handle_generic_error(e)

    @action(detail=False, methods=['get'])
    def trial_eligibility(self, request):
        """Check if user is eligible for a trial period."""
        user = request.user
        profile = self.get_or_create_user_profile(user)
        
        # User is eligible if they haven't used a trial before
        eligible = not profile.trial_start
        
        return Response({
            'eligible': eligible,
            'reason': 'User has already used a trial' if not eligible else 'User is eligible for trial',
            'trial_start': profile.trial_start,
            'trial_end': profile.trial_end,
        })
    
    @action(detail=False, methods=['get'])
    def current(self, request):
        """Get current user's subscription with detailed information."""
        user = request.user
        profile = self.get_or_create_user_profile(user)
        if profile.subscription_plan:
            # Check if subscription is still active
            has_active = profile.has_active_subscription
            
            # Get Stripe subscription details if available
            stripe_subscription_info = None
            stripe_subscription_id = self.get_stripe_subscription_id(profile)
            if stripe_subscription_id:
                try:
                    stripe_sub = stripe.Subscription.retrieve(stripe_subscription_id)
                    stripe_subscription_info = {
                        'current_period_start': stripe_sub.get('current_period_start'),
                        'current_period_end': stripe_sub.get('current_period_end'),
                        'cancel_at_period_end': stripe_sub.get('cancel_at_period_end', False),
                        'trial_end': stripe_sub.get('trial_end'),
                    }
                except stripe.error.StripeError:
                    pass

            return Response({
                'subscription': SubscriptionPlanSerializer(profile.subscription_plan).data,
                'status': profile.subscription_status,
                'start_date': profile.subscription_start_date,
                'end_date': profile.subscription_end_date,
                'cancel_at_period_end': profile.cancel_at_period_end,
                'has_active_subscription': has_active,
                'trial_start': profile.trial_start,
                'trial_end': profile.trial_end,
                'stripe_subscription': stripe_subscription_info,
                'features': {
                    'ad_free': profile.ad_free,
                    'offline_mode': profile.is_offline_mode,
                    'audio_quality': profile.audio_quality,
                    'skip_limit': profile.skip_limit,
                },
            })
        return Response({
            'subscription': None,
            'status': 'none',
            'has_active_subscription': False,
        })