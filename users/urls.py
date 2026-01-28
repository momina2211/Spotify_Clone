from django.urls import path, include
from rest_framework.routers import DefaultRouter
from users.views import UserViewSet, LoginView, UserProfileView, ArtistViewSet

router = DefaultRouter()
router.register('artists', ArtistViewSet, basename='artist')

urlpatterns = [
    path('users', UserViewSet.as_view(), name='user-list-create'),
    path('users/<uuid:pk>', UserViewSet.as_view(), name='user-detail'),
    path('login', LoginView.as_view(), name='login'),
    path('profile', UserProfileView.as_view(), name='user-profile'),
    path('', include(router.urls)),
]