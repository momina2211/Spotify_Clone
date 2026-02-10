from django.core.management.base import BaseCommand
from django.conf import settings
import stripe
from payments.models import SubscriptionPlan

stripe.api_key = settings.STRIPE_SECRET_KEY


class Command(BaseCommand):
    help = 'Create default subscription plans and sync with Stripe'

    def add_arguments(self, parser):
        parser.add_argument(
            '--sync-stripe',
            action='store_true',
            help='Create/update Stripe products and prices',
        )

    def handle(self, *args, **options):
        plans_data = [
            {
                'name': 'Premium Individual',
                'plan_type': SubscriptionPlan.PlanType.INDIVIDUAL,
                'price': 1.35,  # ~Rs 379
                'currency': 'USD',
                'billing_cycle': 'monthly',
                'max_members': 1,
            },
            {
                'name': 'Premium Student',
                'plan_type': SubscriptionPlan.PlanType.STUDENT,
                'price': 0.71,  # ~Rs 199
                'currency': 'USD',
                'billing_cycle': 'monthly',
                'max_members': 1,
            },
            {
                'name': 'Premium Duo',
                'plan_type': SubscriptionPlan.PlanType.DUO,
                'price': 1.85,  # ~Rs 519
                'currency': 'USD',
                'billing_cycle': 'monthly',
                'max_members': 2,
            },
            {
                'name': 'Premium Family',
                'plan_type': SubscriptionPlan.PlanType.FAMILY,
                'price': 2.43,  # ~Rs 679
                'currency': 'USD',
                'billing_cycle': 'monthly',
                'max_members': 6,
            },
        ]

        for plan_data in plans_data:
            plan, created = SubscriptionPlan.objects.get_or_create(
                plan_type=plan_data['plan_type'],
                defaults=plan_data
            )
            if not created:
                # Update existing plan
                for key, value in plan_data.items():
                    setattr(plan, key, value)
                plan.save()
                self.stdout.write(
                    self.style.WARNING(f'Updated plan: {plan.name}')
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(f'Created plan: {plan.name}')
                )

            # Sync with Stripe if requested
            if options['sync_stripe']:
                self.sync_stripe_price(plan)

        self.stdout.write(
            self.style.SUCCESS('Successfully created/updated all subscription plans!')
        )

    def get_stripe_interval(self, billing_cycle):
        """Convert billing cycle to Stripe interval format.
        
        Stripe requires: 'day', 'week', 'month', or 'year'
        Our model uses: 'monthly' or 'annual'
        """
        mapping = {
            'monthly': 'month',
            'annual': 'year',
        }
        return mapping.get(billing_cycle, 'month')  # Default to 'month' if unknown

    def sync_stripe_price(self, plan):
        """Create or update Stripe product and price for a plan."""
        try:
            # Convert price to cents
            price_in_cents = int(float(plan.price) * 100)
            
            # Check if plan already has a Stripe price
            if plan.stripe_price:
                self.stdout.write(
                    self.style.WARNING(f'Plan {plan.name} already has a Stripe price. Skipping...')
                )
                return

            # Create Stripe Product
            product = stripe.Product.create(
                name=plan.name,
                description=f"Spotify Premium - {plan.name}",
                metadata={
                    'plan_id': str(plan.id),
                    'plan_type': plan.plan_type,
                }
            )

            # Convert billing_cycle to Stripe interval format
            stripe_interval = self.get_stripe_interval(plan.billing_cycle)

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

            self.stdout.write(
                self.style.SUCCESS(f'Created Stripe price for {plan.name}: {price.id}')
            )

        except stripe.error.StripeError as e:
            self.stdout.write(
                self.style.ERROR(f'Stripe error for {plan.name}: {str(e)}')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error syncing {plan.name} with Stripe: {str(e)}')
            )
