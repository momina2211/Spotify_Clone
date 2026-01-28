# payments/views.py
from datetime import timezone

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.conf import settings
import stripe
from .models import SubscriptionPlan
from .serializers import SubscriptionPlanSerializer, SubscribeSerializer


class SubscriptionViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request):
        """List all available subscription plans."""
        plans = SubscriptionPlan.objects.filter(is_active=True)
        serializer = SubscriptionPlanSerializer(plans, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def subscribe(self, request):
        """Subscribe to a plan or update existing subscription."""
        serializer = SubscribeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        plan = serializer.validated_data['plan_id']
        user = request.user
        profile = user.profile

        stripe.api_key = settings.STRIPE_SECRET_KEY

        try:
            # Create or get Stripe customer
            if not profile.stripe_customer:
                customer = stripe.Customer.create(
                    email=user.email,
                    name=user.get_full_name() or user.username,
                    metadata={
                        'user_id': user.id,
                        'username': user.username
                    }
                )
                profile.stripe_customer_id = customer.id
                profile.save()
            else:
                customer = stripe.Customer.retrieve(profile.stripe_customer_id)

            # Create subscription
            subscription = stripe.Subscription.create(
                customer=customer.id,
                items=[{'price': plan.stripe_price_id}],
                payment_behavior='default_incomplete',
                expand=['latest_invoice.payment_intent'],
                metadata={
                    'plan_id': str(plan.id),
                    'user_id': user.id
                }
            )

            # Update user profile
            profile.subscription_plan = plan
            profile.subscription_status = 'active'
            profile.subscription_start_date = timezone.now()
            profile.save()
            profile.update_subscription_features()

            return Response({
                'subscription_id': subscription.id,
                'client_secret': subscription.latest_invoice.payment_intent.client_secret,
                'status': 'subscription_created'
            })

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['post'])
    def cancel(self, request):
        """Cancel the current subscription."""
        user = request.user
        profile = user.profile

        if not profile.stripe_subscription_id:
            return Response(
                {'error': 'No active subscription found'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Cancel the subscription at period end
            stripe.Subscription.modify(
                profile.stripe_subscription_id,
                cancel_at_period_end=True
            )

            # Update user profile
            profile.cancel_at_period_end = True
            profile.save()

            return Response({'status': 'subscription_will_cancel'})

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )