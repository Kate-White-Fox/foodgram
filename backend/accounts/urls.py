from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserListView,
    UserDetailView,
    CurrentUserView,
    CurrentUserAvatarView,
    SubscriptionViewSet,
    SetPasswordView
)

router = DefaultRouter()
router.register(r'subscriptions', SubscriptionViewSet, basename='users-subscriptions')

urlpatterns = [
    path('', UserListView.as_view(), name='user-list'),
    path('set_password/', SetPasswordView.as_view(), name='set-password'),
    path('me/', CurrentUserView.as_view(), name='current-user'),
    path('me/avatar/', CurrentUserAvatarView.as_view(), name='user-avatar'),
    path('<int:pk>/', UserDetailView.as_view(), name='user-detail'),
    path('<int:pk>/subscribe/', SubscriptionViewSet.as_view({'post': 'subscribe', 'delete': 'subscribe'}), name='user-subscribe'),
    path('', include(router.urls)),
]
