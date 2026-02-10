from django.core.management.base import BaseCommand
from django.conf import settings
import stripe
from users.models import UserProfile
from payments.models import SubscriptionPlan

stripe.api_key = settings.STRIPE_SECRET_KEY


class Command(BaseCommand):
    help = 'Check and update subscription status from Stripe'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            help='User email to check subscription for',
        )

    def handle(self, *args, **options):
        if not settings.STRIPE_SECRET_KEY:
            self.stdout.write(
                self.style.ERROR('STRIPE_SECRET_KEY is not set.')
            )
            return

        email = options.get('email')
        if email:
            try:
                profile = UserProfile.objects.get(user__email=email)
            except UserProfile.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'User with email {email} not found.')
                )
                return
        else:
            # Get all profiles with subscriptions
            profiles = UserProfile.objects.filter(subscription_plan__isnull=False)
            if not profiles.exists():
                self.stdout.write(
                    self.style.WARNING('No users with subscriptions found.')
                )
                return
            profile = profiles.first()

        self.stdout.write(f'\nChecking subscription for: {profile.user.email}')
        self.stdout.write(f'Current Plan: {profile.subscription_plan.name if profile.subscription_plan else "None"}')
        self.stdout.write(f'Status: {profile.subscription_status}')
        self.stdout.write(f'Stripe Subscription ID: {profile.stripe_subscription_id or "None"}\n')

        if profile.stripe_subscription_id:
            try:
                subscription = stripe.Subscription.retrieve(profile.stripe_subscription_id)
                self.stdout.write(f'Stripe Subscription Status: {subscription["status"]}')
                self.stdout.write(f'Stripe Plan: {subscription["items"]["data"][0]["price"]["id"]}')
                
                # Get the plan from metadata
                plan_id = subscription['metadata'].get('plan_id')
                if plan_id:
                    try:
                        plan = SubscriptionPlan.objects.get(id=plan_id)
                        self.stdout.write(f'Plan from metadata: {plan.name}')
                        
                        # Update if different
                        if profile.subscription_plan != plan:
                            self.stdout.write(
                                self.style.WARNING(f'Updating subscription from {profile.subscription_plan.name} to {plan.name}')
                            )
                            profile.subscription_plan = plan
                            profile.subscription_status = subscription['status']
                            profile.save()
                            profile.update_subscription_features()
                            self.stdout.write(
                                self.style.SUCCESS('Subscription updated!')
                            )
                        else:
                            self.stdout.write(
                                self.style.SUCCESS('Subscription is up to date.')
                            )
                    except SubscriptionPlan.DoesNotExist:
                        self.stdout.write(
                            self.style.ERROR(f'Plan with ID {plan_id} not found in database.')
                        )
            except stripe.error.StripeError as e:
                self.stdout.write(
                    self.style.ERROR(f'Error retrieving Stripe subscription: {str(e)}')
                )
        else:
            self.stdout.write(
                self.style.WARNING('No Stripe subscription ID found. Subscription may not have been processed by webhook yet.')
            )
