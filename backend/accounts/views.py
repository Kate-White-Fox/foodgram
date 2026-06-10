from rest_framework import generics, views, viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from recipes.pagination import CustomPageNumberPagination

from recipes.models import Subscription
from .serializers import (
    UserSerializer,
    UserCreateSerializer,
    SubscriptionAuthorSerializer,
    AvatarUploadSerializer,
)

User = get_user_model()


class UserCreateView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserCreateSerializer
    permission_classes = [AllowAny]


class CurrentUserView(views.APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user, context={'request': request})
        return Response(serializer.data)


class SubscriptionViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """Подписки: список и управление."""
    permission_classes = [IsAuthenticated]
    serializer_class = SubscriptionAuthorSerializer

    def get_queryset(self):
        subscribed_author_ids = Subscription.objects.filter(
            user=self.request.user
        ).values_list('author_id', flat=True)
        return User.objects.filter(id__in=subscribed_author_ids).order_by('id')

    @action(detail=False, url_path='subscriptions')
    def subscriptions(self, request):
        """Список моих подписок."""
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post', 'delete'], url_path='subscribe')
    def subscribe(self, request, pk=None):
        """Подписка / отписка на автора."""
        author = get_object_or_404(User, pk=pk)
        user = request.user

        if user == author:
            return Response(
                {'error': 'Нельзя подписаться на самого себя'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if request.method == 'POST':
            if Subscription.objects.filter(user=user, author=author).exists():
                return Response(
                    {'error': 'Вы уже подписаны'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            Subscription.objects.create(user=user, author=author)
            return Response(
                SubscriptionAuthorSerializer(
                    author, context={'request': request}
                ).data,
                status=status.HTTP_201_CREATED
            )

        elif request.method == 'DELETE':
            subscription = Subscription.objects.filter(user=user, author=author)
            if subscription.exists():
                subscription.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(
                {'error': 'Такой подписки нет'},
                status=status.HTTP_400_BAD_REQUEST
            )


class UserListView(generics.ListCreateAPIView):
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    pagination_class = CustomPageNumberPagination

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return UserCreateSerializer
        return UserSerializer


class UserDetailView(generics.RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]

import logging
logger = logging.getLogger(__name__)

class AvatarUpdateView(views.APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        import traceback
        try:
            user = request.user
            logger.info(f'Avatar PUT FILES: {request.FILES}')
            logger.info(f'Avatar PUT DATA: {request.data}')

            # Проверим что файл загрузился
            if 'avatar' in request.FILES:
                logger.info('Avatar file found in FILES')
            elif 'avatar' in request.data:
                logger.info('Avatar found in data')
            else:
                logger.error('No avatar in request!')
                return Response({'error': 'no avatar'}, status=400)

            serializer = AvatarUploadSerializer(user, data=request.data, partial=True)
            if serializer.is_valid():
                instance = serializer.save()
                logger.info(f'Avatar saved: {instance.avatar.url}')
                return Response(serializer.data)
            logger.error(f'Serializer errors: {serializer.errors}')
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f'Avatar PUT error: {e}')
            traceback.print_exc()
            return Response({'error': str(e)}, status=500)