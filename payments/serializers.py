# payments/serializers.py
from rest_framework import serializers
from .models import SubscriptionPlan
from users.models import UserProfile


class SubscriptionPlanSerializer(serializers.ModelSerializer):
    features = serializers.SerializerMethodField()

    class Meta:
        model = SubscriptionPlan
        fields = [
            'id', 'name', 'plan_type', 'price', 'currency',
            'billing_cycle', 'features', 'is_active'
        ]

    def get_features(self, obj):
        return obj.get_features()


class SubscribeSerializer(serializers.Serializer):
    plan_id = serializers.UUIDField(required=True)
    payment_method_id = serializers.CharField(required=False)

    def validate_plan_id(self, value):
        try:
            plan = SubscriptionPlan.objects.get(id=value, is_active=True)
            return plan
        except SubscriptionPlan.DoesNotExist:
            raise serializers.ValidationError("Invalid plan ID or plan is not active")