from django.urls import path
from users.views import UserViewSet,LoginView,UserProfileView

urlpatterns = [
    path('users', UserViewSet.as_view(), name='user-list-create'),
    path('users/<uuid:pk>', UserViewSet.as_view(), name='user-detail'),
    path('login', LoginView.as_view(), name='login'),
    path('profile', UserProfileView.as_view(), name='user-profile'),
]