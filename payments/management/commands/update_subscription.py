from django.core.management.base import BaseCommand
from users.models import UserProfile
from payments.models import SubscriptionPlan


class Command(BaseCommand):
    help = 'Manually update user subscription plan'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            required=True,
            help='User email',
        )
        parser.add_argument(
            '--plan-type',
            type=str,
            required=True,
            choices=['student', 'individual', 'duo', 'family'],
            help='Plan type to set',
        )

    def handle(self, *args, **options):
        email = options['email']
        plan_type = options['plan_type']

        try:
            profile = UserProfile.objects.get(user__email=email)
        except UserProfile.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'User with email {email} not found.')
            )
            return

        try:
            plan = SubscriptionPlan.objects.get(plan_type=plan_type)
        except SubscriptionPlan.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'Plan with type {plan_type} not found.')
            )
            return

        old_plan = profile.subscription_plan.name if profile.subscription_plan else 'None'
        profile.subscription_plan = plan
        profile.subscription_status = 'trialing' if plan_type in ['student', 'individual'] else 'active'
        profile.save()
        profile.update_subscription_features()

        self.stdout.write(
            self.style.SUCCESS(
                f'Updated subscription for {email} from {old_plan} to {plan.name}'
            )
        )
