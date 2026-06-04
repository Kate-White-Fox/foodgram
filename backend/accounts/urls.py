from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserCreateView, CurrentUserView, SubscriptionViewSet

router = DefaultRouter()
router.register(r'', SubscriptionViewSet, basename='users')

urlpatterns = [
    path('', include(router.urls)),
    path('register/', UserCreateView.as_view(), name='user-register'),
    path('me/', CurrentUserView.as_view(), name='current-user'),
]
