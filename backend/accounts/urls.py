from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserListView, CurrentUserView, SubscriptionViewSet

router = DefaultRouter()
router.register(r'', SubscriptionViewSet, basename='users-subscriptions')

urlpatterns = [
    path('', UserListView.as_view(), name='user-list-create'),
    path('me/', CurrentUserView.as_view(), name='current-user'),
    path('<int:pk>/subscribe/', SubscriptionViewSet.as_view({'post': 'subscribe', 'delete': 'subscribe'}), name='user-subscribe'),
    path('subscriptions/', SubscriptionViewSet.as_view({
        'get': 'subscriptions'
    }), name='user-subscriptions'),
]

