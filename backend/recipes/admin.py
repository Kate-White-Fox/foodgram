from django.contrib import admin
from .models import (
    Ingredient,
    Tag,
    Recipe,
    RecipeIngredient,
    Follow,
    Favorite,
    ShoppingList
)


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author', 'count_favorites')
    search_fields = ('name', 'author__username', 'author__email')
    list_filter = ('tags', 'author', 'name')
    inlines = (RecipeIngredientInline,)

    def count_favorites(self, obj):
        return obj.favorited_by.count()
    count_favorites.short_description = 'Добавлений в избранное'


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)


admin.site.register(Tag)
admin.site.register(Follow)
admin.site.register(Favorite)
admin.site.register(ShoppingList)
