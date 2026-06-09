from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator
from recipes.models import Subscription, Recipe
from rest_framework.validators import UniqueValidator

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()
    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name', 'last_name', 'is_subscribed', 'avatar')

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return Subscription.objects.filter(user=request.user, author=obj).exists()

    def get_avatar(self, obj):
        """Возвращает URL аватара строкой или None (тесты ожидают null как валидный string)"""
        if obj.avatar and hasattr(obj.avatar, 'url'):
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.avatar.url)
            return obj.avatar.url
        return None


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    username = serializers.CharField(
	max_length=150,
        validators=[
            RegexValidator(
                regex=r'^[\w.@+-]+\Z',
                message='Username can only contain letters, digits and @/./+/-/_'
            ),
            UniqueValidator(
                queryset=User.objects.all(),
                message='Пользователь с таким username уже существует.'
            )
        ]
    )
    email = serializers.EmailField(
        validators=[
            UniqueValidator(
                queryset=User.objects.all(),
                message='Пользователь с таким email уже существует.'
            )
        ]
    )

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name', 'last_name', 'password')
        extra_kwargs = {
            'username': {'required': True, 'allow_blank': False},
            'first_name': {'required': True, 'allow_blank': False},
            'last_name': {'required': True, 'allow_blank': False},
            'email': {'required': True},
            'password': {'required': True},
        }

    def validate_username(self, value):
        """Запрещаем username = 'me' (требуют тесты)"""
        if value.lower() == 'me':
            raise serializers.ValidationError(
                'Username "me" is not allowed.'
            )
        return value

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user


class RecipeShortSerializer(serializers.ModelSerializer):
    """Краткая информация о рецепте для подписок."""
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class SubscriptionAuthorSerializer(serializers.ModelSerializer):
    """Отображение автора в подписках."""
    is_subscribed = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            'is_subscribed', 'recipes_count', 'recipes',
        )
        read_only_fields = ('__all__',)

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Subscription.objects.filter(
                user=request.user, author=obj
            ).exists()
        return False

    def get_recipes_count(self, obj):
        return obj.recipes.count()

    def get_recipes(self, obj):
        request = self.context.get('request')
        limit = request.query_params.get('recipes_limit')
        recipes_qs = obj.recipes.all()
        try:
            limit = int(limit) if limit else 3
        except (ValueError, TypeError):
            limit = 3
        return RecipeShortSerializer(
            recipes_qs[:limit],
            many=True,
            context={'request': request}
        ).data

