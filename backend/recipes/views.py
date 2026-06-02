from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.filters import SearchFilter
from rest_framework.permissions import SAFE_METHODS, BasePermission

from .models import Recipe, Tag, Ingredient, RecipeIngredient, ShoppingList, Favorite
from .serializers import (
    TagSerializer, IngredientSerializer,
    ShoppingCartSerializer, RecipeReadSerializer, RecipeWriteSerializer
)
from .pagination import CustomPageNumberPagination


class AuthorOrReadOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.method in SAFE_METHODS or obj.author == request.user


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.select_related('author').prefetch_related(
        'tags',
        'recipe_ingredients__ingredient',
        'favorites',
        'shoppingcarts'
    )

    pagination_class = CustomPageNumberPagination
    permission_classes = [AuthorOrReadOnly]

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return RecipeReadSerializer
        return RecipeWriteSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_queryset(self):
        queryset = Recipe.objects.all().order_by('-pub_date')

        # Фильтр по тегам
        tags = self.request.query_params.getlist('tags')
        if tags:
            queryset = queryset.filter(tags__slug__in=tags).distinct()

        # Фильтр по автору
        author = self.request.query_params.get('author')
        if author:
            queryset = queryset.filter(author_id=author)

        # Фильтр по избранному
        is_favorited = self.request.query_params.get('is_favorited')
        if is_favorited and self.request.user.is_authenticated:
            queryset = queryset.filter(favorited_by__user=self.request.user)

        # Фильтр по корзине покупок
        is_in_shopping_cart = self.request.query_params.get('is_in_shopping_cart')
        if is_in_shopping_cart and self.request.user.is_authenticated:
            queryset = queryset.filter(in_shopping_list__user=self.request.user)

        return queryset

    @action(
        detail=True,
        methods=['get', 'post', 'delete'],
        permission_classes=[IsAuthenticated],
        url_path='favorite'
    )
    def favorite(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        user = request.user

        if request.method == 'GET':
            is_favorited = Favorite.objects.filter(user=user, recipe=recipe).exists()
            return Response({'is_favorited': is_favorited})

        if request.method == 'POST':
            if Favorite.objects.filter(user=user, recipe=recipe).exists():
                return Response(
                    {'errors': 'Рецепт уже в избранном'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            Favorite.objects.create(user=user, recipe=recipe)
            serializer = self.get_serializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            Favorite.objects.filter(user=user, recipe=recipe).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated]
    )
    def shopping_cart(self, request, pk):
        user = request.user
        recipe = get_object_or_404(Recipe, id=pk)

        if request.method == 'POST':
            if ShoppingList.objects.filter(user=user, recipe=recipe).exists():
                return Response(
                    {'errors': 'Рецепт уже в корзине'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            ShoppingList.objects.create(user=user, recipe=recipe)
            serializer = ShoppingCartSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            obj = ShoppingList.objects.filter(user=user, recipe=recipe)
            if obj.exists():
                obj.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(
                {'errors': 'Рецепта нет в корзине'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        user = request.user

        cart_recipes = Recipe.objects.filter(in_shopping_list__user=user)
        if not cart_recipes.exists():
            return HttpResponse(
                "Ваш список покупок пуст",
                content_type='text/plain; charset=utf-8'
            )

        ingredients = (
            RecipeIngredient.objects
            .filter(recipe__in_shopping_list__user=user)
            .values('ingredient__name', 'ingredient__measurement_unit')
            .annotate(total_amount=Sum('amount'))
            .order_by('ingredient__name')
        )

        content = [f'Список покупок для {user.get_full_name() or user.username}:\n']
        for item in ingredients:
            content.append(
                f"• {item['ingredient__name']} ({item['ingredient__measurement_unit']}) "
                f"— {item['total_amount']}"
            )

        response_content = "\n".join(content)
        filename = f'{user.username}_shopping_list.txt'
        response = HttpResponse(
            response_content,
            content_type='text/plain; charset=utf-8'
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

    @action(
        detail=True,
        methods=['get'],
        url_path='get-link',
        permission_classes=[AllowAny]
    )
    def get_link(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)

        scheme = request.scheme 
        host = request.get_host()

        link = f"{scheme}://{host}/recipes/{recipe.id}/"

        return Response({
            'short-link': link,
            'short_link': link,
            'link': link
        }, status=status.HTTP_200_OK)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    filter_backends = (SearchFilter,)
    search_fields = ('^name',)
