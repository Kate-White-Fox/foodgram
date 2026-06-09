import base64
from django.core.files.base import ContentFile
from rest_framework import serializers
from rest_framework.reverse import reverse
from recipes.models import Ingredient, Tag, Recipe, RecipeIngredient, ShoppingList, Favorite


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
        return super().to_internal_value(data)


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeReadSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    author = serializers.SerializerMethodField()
    author_id = serializers.ReadOnlyField(source='author.id')
    ingredients = serializers.SerializerMethodField()
    image = Base64ImageField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    is_author = serializers.SerializerMethodField()
    share_link = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'author_id', 'ingredients',
            'is_in_shopping_cart', 'is_favorited', 'is_author',
            'share_link',
            'name', 'image', 'text', 'cooking_time',
        )
        read_only_fields = fields

    def get_ingredients(self, obj):
        queryset = obj.ingredient_list.all()
        return RecipeIngredientSerializer(queryset, many=True).data

    def get_author(self, obj):
        request = self.context.get('request')
        is_subscribed = False
        if request and request.user.is_authenticated:
            is_subscribed = False 

        return {
            "email": obj.author.email,
            "id": obj.author.id,
            "username": obj.author.username,
            "first_name": obj.author.first_name,
            "last_name": obj.author.last_name,
            "is_subscribed": is_subscribed  # Фронтенд может ждать это поле
        }

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return ShoppingList.objects.filter(user=request.user, recipe=obj).exists()

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return Favorite.objects.filter(user=request.user, recipe=obj).exists()

    def get_is_author(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return obj.author_id == request.user.id

    def get_share_link(self, obj):
        request = self.context.get('request')
        if not request:
            return None
        relative_link = reverse('recipe-detail', args=[obj.id], request=request)
        return request.build_absolute_uri(relative_link)


class RecipeWriteSerializer(serializers.ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True
    )
    ingredients = serializers.ListField(
        child=serializers.DictField(),
        write_only=True
    )
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'ingredients',
            'name', 'image', 'text', 'cooking_time',
        )
        read_only_fields = ('id',)

    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients_data = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)

        for ingredient_item in ingredients_data:
            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredient_id=ingredient_item['id'],
                amount=ingredient_item['amount']
            )

        return recipe

    def update(self, instance, validated_data):
        tags = validated_data.pop('tags', None)
        ingredients_data = validated_data.pop('ingredients', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if tags is not None:
            instance.tags.set(tags)

        if ingredients_data is not None:
            instance.ingredient_list.all().delete()
            for ingredient_item in ingredients_data:
                RecipeIngredient.objects.create(
                    recipe=instance,
                    ingredient_id=ingredient_item['id'],
                    amount=ingredient_item['amount']
                )

        return instance


class RecipeSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    author = serializers.SerializerMethodField()
    author_id = serializers.ReadOnlyField(source='author.id')
    ingredients = serializers.SerializerMethodField()
    image = Base64ImageField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    is_author = serializers.SerializerMethodField()
    share_link = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'author_id', 'ingredients',
            'is_in_shopping_cart', 'is_favorited', 'is_author',
            'share_link',
            'name', 'image', 'text', 'cooking_time'
        )

    def get_ingredients(self, obj):
        queryset = obj.ingredient_list.all()
        return RecipeIngredientSerializer(queryset, many=True).data

    def get_author(self, obj):
        request = self.context.get('request')
        is_subscribed = False
        if request and request.user.is_authenticated:
            is_subscribed = False 

        return {
            "email": obj.author.email,
            "id": obj.author.id,
            "username": obj.author.username,
            "first_name": obj.author.first_name,
            "last_name": obj.author.last_name,
            "is_subscribed": is_subscribed  # Фронтенд может ждать это поле
        }

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return ShoppingList.objects.filter(user=request.user, recipe=obj).exists()

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return Favorite.objects.filter(user=request.user, recipe=obj).exists()

    def get_is_author(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return obj.author_id == request.user.id

    def get_share_link(self, obj):
        request = self.context.get('request')
        if not request:
            return None
        relative_link = reverse('recipe-detail', args=[obj.id], request=request)
        return request.build_absolute_uri(relative_link)


class ShoppingCartSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = ('id', 'name', 'image', 'cooking_time')


class RecipeCreateSerializer(serializers.ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True
    )
    ingredients = serializers.ListField(
        child=serializers.DictField(),
        write_only=True
    )
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'ingredients',
            'name', 'image', 'text', 'cooking_time'
        )

    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients_data = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)

        for ingredient_item in ingredients_data:
            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredient_id=ingredient_item['id'],
                amount=ingredient_item['amount']
            )

        return recipe

    def update(self, instance, validated_data):
        tags = validated_data.pop('tags', None)
        ingredients_data = validated_data.pop('ingredients', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if tags is not None:
            instance.tags.set(tags)

        if ingredients_data is not None:
            instance.ingredient_list.all().delete()
            for ingredient_item in ingredients_data:
                RecipeIngredient.objects.create(
                    recipe=instance,
                    ingredient_id=ingredient_item['id'],
                    amount=ingredient_item['amount']
                )

        return instance
