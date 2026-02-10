from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SubscriptionViewSet
from .webhooks import stripe_webhook

router = DefaultRouter()
router.register(r'subscriptions', SubscriptionViewSet, basename='subscription')

urlpatterns = [
    path('', include(router.urls)),
    path('webhooks/stripe/', stripe_webhook, name='stripe_webhook'),
]
