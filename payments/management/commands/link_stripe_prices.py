from django.core.management.base import BaseCommand
from django.conf import settings
import stripe
from payments.models import SubscriptionPlan

stripe.api_key = settings.STRIPE_SECRET_KEY


class Command(BaseCommand):
    help = 'Link existing Stripe Price IDs to subscription plans'

    def add_arguments(self, parser):
        parser.add_argument(
            '--price-ids',
            type=str,
            help='Comma-separated list of plan_type:price_id pairs (e.g., "student:price_xxx,individual:price_yyy")',
        )

    def handle(self, *args, **options):
        if not settings.STRIPE_SECRET_KEY:
            self.stdout.write(
                self.style.ERROR('STRIPE_SECRET_KEY is not set in your environment variables.')
            )
            return

        # Default price IDs (update these with your actual Stripe Price IDs)
        price_ids = {
            'student': 'price_1SwMyZAlEqDf6TDF7LIDpKgN',  # Premium Student
            'individual': None,  # Update with your Premium Individual price ID
            'duo': None,  # Update with your Premium Duo price ID
            'family': None,  # Update with your Premium Family price ID
        }

        # Check environment variables for price IDs
        import os
        env_price_ids = {
            'student': os.environ.get('STRIPE_PREMIUM_STUDENT_PRICE_ID'),
            'individual': os.environ.get('STRIPE_PREMIUM_INDIVIDUAL_PRICE_ID'),
            'duo': os.environ.get('STRIPE_PREMIUM_DUO_PRICE_ID'),
            'family': os.environ.get('STRIPE_PREMIUM_FAMILY_PRICE_ID'),
        }
        
        # Use env vars if they're price IDs (start with price_)
        for plan_type, env_price_id in env_price_ids.items():
            if env_price_id and env_price_id.startswith('price_'):
                price_ids[plan_type] = env_price_id
                self.stdout.write(
                    self.style.SUCCESS(f'Found {plan_type} price ID from environment: {env_price_id}')
                )

        # Override with command line arguments if provided
        if options['price_ids']:
            for pair in options['price_ids'].split(','):
                plan_type, price_id = pair.split(':')
                price_ids[plan_type.strip()] = price_id.strip()

        # Link prices to plans
        for plan_type, price_id in price_ids.items():
            if not price_id:
                self.stdout.write(
                    self.style.WARNING(f'Skipping {plan_type} - no price ID provided')
                )
                continue

            try:
                plan = SubscriptionPlan.objects.get(plan_type=plan_type)
                
                # Verify the price exists in Stripe
                try:
                    stripe_price = stripe.Price.retrieve(price_id)
                    self.stdout.write(
                        self.style.SUCCESS(f'Found Stripe price: {stripe_price.id} for {stripe_price.product}')
                    )
                except stripe.error.StripeError as e:
                    self.stdout.write(
                        self.style.ERROR(f'Stripe price {price_id} not found: {str(e)}')
                    )
                    continue

                # Update plan with Stripe price ID
                plan.stripe_price_id_string = price_id
                plan.save()

                self.stdout.write(
                    self.style.SUCCESS(f'Linked {plan.name} to Stripe price: {price_id}')
                )

            except SubscriptionPlan.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Plan with type {plan_type} not found')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error linking {plan_type}: {str(e)}')
                )

        self.stdout.write(
            self.style.SUCCESS('Finished linking Stripe prices!')
        )
