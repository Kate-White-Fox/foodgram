from django.urls import path, include
from rest_framework.routers import DefaultRouter
from djoser.views import UserViewSet
from .views import UserListView, UserDetailView, CurrentUserView, SubscriptionViewSet, AvatarUpdateView

router = DefaultRouter()
router.register(r'', SubscriptionViewSet, basename='users-subscriptions')

urlpatterns = [
    path('me/avatar/', AvatarUpdateView.as_view(), name='avatar-update'),
    path('me/', CurrentUserView.as_view(), name='current-user'),
    path('', UserListView.as_view(), name='user-list-create'),
    path('<int:pk>/', UserDetailView.as_view(), name='user-detail'),
    path('<int:pk>/subscribe/', SubscriptionViewSet.as_view({'post': 'subscribe', 'delete': 'subscribe'}), name='user-subscribe'),
    path('subscriptions/', SubscriptionViewSet.as_view({'get': 'subscriptions'}), name='user-subscriptions'),
    path('set_password/', UserViewSet.as_view({'post': 'set_password'}), name='user-set-password'),
]
