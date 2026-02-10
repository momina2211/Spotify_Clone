from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SubscriptionViewSet
from .webhooks import stripe_webhook

router = DefaultRouter()
router.register(r'subscriptions', SubscriptionViewSet, basename='subscription')

urlpatterns = [
    path('payments/', include(router.urls)),
    path('payments/webhooks/stripe/', stripe_webhook, name='stripe_webhook'),
]
