from django.core.management.base import BaseCommand
from django.conf import settings
import os
import stripe
from payments.models import SubscriptionPlan

stripe.api_key = settings.STRIPE_SECRET_KEY


class Command(BaseCommand):
    help = 'Get Stripe Price ID from Product ID or list all prices for a product'

    def add_arguments(self, parser):
        parser.add_argument(
            '--product-id',
            type=str,
            help='Stripe Product ID (starts with prod_) to get prices for',
        )
        parser.add_argument(
            '--plan-type',
            type=str,
            choices=['student', 'individual', 'duo', 'family'],
            help='Plan type to get price ID for (uses product from .env if available)',
        )

    def handle(self, *args, **options):
        if not settings.STRIPE_SECRET_KEY:
            self.stdout.write(
                self.style.ERROR('STRIPE_SECRET_KEY is not set in your environment variables.')
            )
            return

        product_id = options.get('product_id')
        plan_type = options.get('plan_type')

        # If plan_type is provided, try to get product ID from env or plan
        if plan_type and not product_id:
            # Check if there's a product ID in env for this plan
            env_key = f'STRIPE_PREMIUM_{plan_type.upper()}_PRICE_ID'
            product_id = os.environ.get(env_key)
            
            # If it's actually a price ID (starts with price_), retrieve it
            if product_id and product_id.startswith('price_'):
                try:
                    price = stripe.Price.retrieve(product_id)
                    self.stdout.write(
                        self.style.SUCCESS(f'\n✅ Found Price ID for {plan_type}:')
                    )
                    self.stdout.write(f'   Price ID: {price.id}')
                    self.stdout.write(f'   Product ID: {price.product}')
                    self.stdout.write(f'   Amount: {price.unit_amount / 100} {price.currency.upper()}')
                    self.stdout.write(f'   Interval: {price.recurring.interval if price.recurring else "one-time"}')
                    
                    # Link it to the plan
                    try:
                        plan = SubscriptionPlan.objects.get(plan_type=plan_type)
                        plan.stripe_price_id_string = price.id
                        plan.save()
                        self.stdout.write(
                            self.style.SUCCESS(f'\n✅ Linked {plan.name} to Price ID: {price.id}')
                        )
                    except SubscriptionPlan.DoesNotExist:
                        self.stdout.write(
                            self.style.WARNING(f'\n⚠️  Plan {plan_type} not found in database')
                        )
                    return
                except stripe.error.StripeError as e:
                    self.stdout.write(
                        self.style.ERROR(f'Error retrieving price: {str(e)}')
                    )
                    return
            
            # If it's a product ID, continue to list prices
            if product_id and product_id.startswith('prod_'):
                pass  # Continue to list prices below
            else:
                self.stdout.write(
                    self.style.ERROR(f'No product ID found for {plan_type}. Use --product-id to specify.')
                )
                return

        if not product_id:
            self.stdout.write(
                self.style.ERROR('Please provide either --product-id or --plan-type')
            )
            return

        # List all prices for the product
        try:
            self.stdout.write(f'\n📦 Fetching prices for product: {product_id}\n')
            
            # Get product details
            product = stripe.Product.retrieve(product_id)
            self.stdout.write(f'Product: {product.name}')
            self.stdout.write(f'Description: {product.description or "N/A"}\n')
            
            # List all prices for this product
            prices = stripe.Price.list(product=product_id, limit=100)
            
            if not prices.data:
                self.stdout.write(
                    self.style.WARNING('No prices found for this product.')
                )
                return

            self.stdout.write(f'Found {len(prices.data)} price(s):\n')
            
            for i, price in enumerate(prices.data, 1):
                self.stdout.write(f'{i}. Price ID: {self.style.SUCCESS(price.id)}')
                self.stdout.write(f'   Amount: {price.unit_amount / 100} {price.currency.upper()}')
                if price.recurring:
                    self.stdout.write(f'   Interval: {price.recurring.interval}')
                    if hasattr(price.recurring, 'trial_period_days') and price.recurring.trial_period_days:
                        self.stdout.write(f'   Trial: {price.recurring.trial_period_days} days')
                self.stdout.write(f'   Active: {price.active}')
                self.stdout.write('')

            # If plan_type is provided, ask which one to link
            if plan_type:
                self.stdout.write(
                    self.style.WARNING(f'\n💡 To link a price to {plan_type} plan, use:')
                )
                self.stdout.write(
                    f'   python manage.py link_stripe_prices --price-ids "{plan_type}:PRICE_ID_HERE"'
                )

        except stripe.error.StripeError as e:
            self.stdout.write(
                self.style.ERROR(f'Error: {str(e)}')
            )
