from django.db.models import Sum
from django.http import HttpResponse
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

from .models import Recipe, Tag, Ingredient, RecipeIngredient
from .serializers import RecipeSerializer, TagSerializer, IngredientSerializer
from .pagination import CustomPageNumberPagination


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all().order_by('-id')
    serializer_class = RecipeSerializer
    pagination_class = CustomPageNumberPagination

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated]
    )
    def export_shopping_list(self, request):
        user = request.user
        ingredients = RecipeIngredient.objects.filter(
            recipe__shopping_recipe__user=user
        ).values(
            'ingredient__name', 
            'ingredient__measurement_unit'
        ).annotate(total_amount=Sum('amount'))

        content = (
            f"Список покупок для {user.get_full_name() or user.username}\n\n"
        )
        for item in ingredients:
            content += (
                f"• {item['ingredient__name']} ({item['ingredient__measurement_unit']}) "
                f"— {item['total_amount']}\n"
            )

        response = HttpResponse(
            content,
            content_type='text/plain; charset=utf-8'
        )
        response['Content-Disposition'] = 'attachment; filename="shopping_list.txt"'
        return response


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
