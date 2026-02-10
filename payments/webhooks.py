# payments/webhooks.py
import stripe
import json
from datetime import timedelta
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.conf import settings
from django.utils import timezone
from users.models import User, UserProfile
from payments.models import SubscriptionPlan

stripe.api_key = settings.STRIPE_SECRET_KEY


@csrf_exempt
@require_POST
def stripe_webhook(request):
    """Handle Stripe webhook events."""
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    endpoint_secret = settings.DJSTRIPE_WEBHOOK_SECRET

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError:
        # Invalid payload
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        # Invalid signature
        return HttpResponse(status=400)

    # Handle the event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        handle_checkout_session(session)
    elif event['type'] == 'payment_intent.succeeded':
        # Handle one-time payment success
        payment_intent = event['data']['object']
        handle_payment_intent_succeeded(payment_intent)
    elif event['type'] == 'customer.subscription.created':
        subscription = event['data']['object']
        handle_subscription_created(subscription)
    elif event['type'] == 'customer.subscription.updated':
        subscription = event['data']['object']
        handle_subscription_updated(subscription)
    elif event['type'] == 'customer.subscription.deleted':
        subscription = event['data']['object']
        handle_subscription_deleted(subscription)
    elif event['type'] == 'invoice.payment_succeeded':
        invoice = event['data']['object']
        handle_invoice_payment_succeeded(invoice)
    elif event['type'] == 'invoice.payment_failed':
        invoice = event['data']['object']
        handle_invoice_payment_failed(invoice)

    return JsonResponse({'status': 'success'})


def handle_checkout_session(session):
    """Handle successful checkout session (both subscription and one-time payment)."""
    user_id = session['metadata'].get('user_id')
    plan_id = session['metadata'].get('plan_id')
    payment_type = session['metadata'].get('payment_type', 'subscription')
    
    if not user_id or not plan_id:
        return

    try:
        user = User.objects.get(id=user_id)
        plan = SubscriptionPlan.objects.get(id=plan_id)
        profile = user.profile

        # Handle one-time payment
        if payment_type == 'one_time':
            # For one-time payment, activate subscription for 1 year
            profile.subscription_plan = plan
            profile.subscription_status = 'active'
            profile.subscription_start_date = timezone.now()
            profile.subscription_end_date = timezone.now() + timedelta(days=365)  # 1 year from now
            profile.save()
            profile.update_subscription_features()
            return

        # Handle subscription payment
        # Update profile with subscription plan
        profile.subscription_plan = plan
        # Check if subscription has trial period - if so, status should be 'trialing'
        subscription_id = session.get('subscription')
        if subscription_id:
            try:
                subscription = stripe.Subscription.retrieve(subscription_id)
                profile.subscription_status = subscription.get('status', 'active')
                if subscription.get('trial_end'):
                    profile.trial_start = timezone.datetime.fromtimestamp(subscription.get('trial_start', subscription['created']), tz=timezone.utc) if isinstance(subscription.get('trial_start', subscription['created']), (int, float)) else timezone.now()
                    profile.trial_end = timezone.datetime.fromtimestamp(subscription['trial_end'], tz=timezone.utc) if isinstance(subscription['trial_end'], (int, float)) else timezone.now() + timedelta(days=30)
            except stripe.error.StripeError:
                # Fallback to 'active' if we can't retrieve subscription
                profile.subscription_status = 'active'
        else:
            profile.subscription_status = 'active'
        profile.subscription_start_date = timezone.now()
        
        # Get customer ID from session
        customer_id = session.get('customer')
        if customer_id:
            # Store customer ID (you might want to use dj-stripe Customer model)
            # For now, we'll store it as a string
            profile.stripe_customer_id = customer_id

        # Get subscription ID if available
        subscription_id = session.get('subscription')
        if subscription_id:
            profile.stripe_subscription_id = subscription_id

        profile.save()
        profile.update_subscription_features()

    except (User.DoesNotExist, SubscriptionPlan.DoesNotExist) as e:
        print(f"Error in handle_checkout_session: {e}")


def handle_subscription_created(subscription):
    """Handle subscription creation."""
    user_id = subscription['metadata'].get('user_id')
    plan_id = subscription['metadata'].get('plan_id')
    
    if not user_id or not plan_id:
        return

    try:
        user = User.objects.get(id=user_id)
        plan = SubscriptionPlan.objects.get(id=plan_id)
        profile = user.profile

        profile.subscription_plan = plan
        profile.subscription_status = subscription['status']
        profile.subscription_start_date = timezone.datetime.fromtimestamp(subscription['created'], tz=timezone.utc) if isinstance(subscription['created'], (int, float)) else timezone.now()
        
        if subscription.get('trial_end'):
            trial_end_ts = subscription['trial_end']
            profile.trial_end = timezone.datetime.fromtimestamp(trial_end_ts, tz=timezone.utc) if isinstance(trial_end_ts, (int, float)) else timezone.now() + timedelta(days=30)
            trial_start_ts = subscription.get('trial_start')
            profile.trial_start = timezone.datetime.fromtimestamp(trial_start_ts, tz=timezone.utc) if trial_start_ts and isinstance(trial_start_ts, (int, float)) else timezone.now()
        
        if subscription.get('current_period_end'):
            period_end_ts = subscription['current_period_end']
            profile.subscription_end_date = timezone.datetime.fromtimestamp(period_end_ts, tz=timezone.utc) if isinstance(period_end_ts, (int, float)) else timezone.now() + timedelta(days=30)

        profile.stripe_subscription_id = subscription['id']
        profile.save()
        profile.update_subscription_features()

    except (User.DoesNotExist, SubscriptionPlan.DoesNotExist) as e:
        print(f"Error in handle_subscription_created: {e}")


def handle_subscription_updated(subscription):
    """Handle subscription updates."""
    user_id = subscription['metadata'].get('user_id')
    
    if not user_id:
        return

    try:
        user = User.objects.get(id=user_id)
        profile = user.profile

        profile.subscription_status = subscription['status']
        
        if subscription.get('current_period_end'):
            period_end_ts = subscription['current_period_end']
            profile.subscription_end_date = timezone.datetime.fromtimestamp(period_end_ts, tz=timezone.utc) if isinstance(period_end_ts, (int, float)) else timezone.now() + timedelta(days=30)
        
        if subscription.get('cancel_at_period_end'):
            profile.cancel_at_period_end = subscription['cancel_at_period_end']

        profile.save()

    except User.DoesNotExist as e:
        print(f"Error in handle_subscription_updated: {e}")


def handle_subscription_deleted(subscription):
    """Handle subscription cancellation."""
    user_id = subscription['metadata'].get('user_id')
    
    if not user_id:
        return

    try:
        user = User.objects.get(id=user_id)
        profile = user.profile

        profile.subscription_status = 'canceled'
        profile.cancel_at_period_end = False
        profile.stripe_subscription_id = None
        profile.save()

    except User.DoesNotExist as e:
        print(f"Error in handle_subscription_deleted: {e}")


def handle_invoice_payment_succeeded(invoice):
    """Handle successful invoice payment."""
    subscription_id = invoice.get('subscription')
    if not subscription_id:
        return

    # Update subscription end date based on invoice
    # This is handled in subscription.updated event, but we can add additional logic here
    pass


def handle_invoice_payment_failed(invoice):
    """Handle failed invoice payment."""
    subscription_id = invoice.get('subscription')
    if not subscription_id:
        return

    try:
        # Find user by subscription ID
        profile = UserProfile.objects.filter(stripe_subscription_id=subscription_id).first()
        if profile:
            profile.subscription_status = 'past_due'
            profile.save()
    except Exception as e:
        print(f"Error in handle_invoice_payment_failed: {e}")


def handle_payment_intent_succeeded(payment_intent):
    """Handle successful one-time payment."""
    # This is handled in checkout.session.completed, but we can add additional logic here if needed
    pass
