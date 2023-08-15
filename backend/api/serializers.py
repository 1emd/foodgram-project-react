# flake8: noqa
from django.core.validators import MinValueValidator
from django.shortcuts import get_object_or_404
from drf_extra_fields.fields import Base64ImageField
from rest_framework.exceptions import ValidationError
from rest_framework.relations import PrimaryKeyRelatedField
from rest_framework.serializers import (CharField, IntegerField,
                                        ModelSerializer, ReadOnlyField,
                                        SerializerMethodField)

from api.constants import (DUPLICATE_INGREDIENT_MESSAGE,
                           DUPLICATE_TAGS_MESSAGE, INVALID_AMOUNT_MESSAGE,
                           INVALID_COOKING_TIME_MESSAGE,
                           MISSING_INGREDIENT_MESSAGE, MISSING_TAG_MESSAGE)
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)
from users.models import Subscription, User


class CustomUserCreateSerializer(ModelSerializer):
    password = CharField(write_only=True)

    class Meta:
        model = User
        fields = ('email', 'username', 'first_name', 'last_name', 'password')

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class CustomUserSerializer(ModelSerializer):
    is_subscribed = SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed')

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Subscription.objects.filter(
                user=request.user, author=obj).exists()
        return False


class RecipeMinifiedSerializer(ModelSerializer):

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time',)


class SubscriptionSerializer(ModelSerializer):
    is_subscribed = SerializerMethodField()
    recipes = SerializerMethodField()
    recipes_count = SerializerMethodField()

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed', 'recipes', 'recipes_count')
        read_only_fields = ('email', 'username', 'first_name', 'last_name',
                            'is_subscribed', 'recipes', 'recipes_count')

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        user = request.user
        if user.is_anonymous:
            return False
        return Subscription.objects.filter(user=user, author=obj).exists()

    def get_recipes(self, obj):
        request = self.context.get('request')
        recipes_limit = request.query_params.get('recipes_limit')
        recipes = obj.recipes.all()

        if recipes_limit:
            recipes = recipes[:int(recipes_limit)]

        return RecipeMinifiedSerializer(
            recipes, many=True, context={'request': request}).data

    def get_recipes_count(self, obj):
        return obj.recipes.count()


class IngredientSerializer(ModelSerializer):

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit',)


class TagSerializer(ModelSerializer):

    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug',)


class RecipeIngredientSerializer(ModelSerializer):
    id = IntegerField()
    name = ReadOnlyField(
        source='ingredient.name')
    measurement_unit = ReadOnlyField(
        source='ingredient.measurement_unit')
    amount = IntegerField(
        validators=[MinValueValidator(
            1, message=INVALID_AMOUNT_MESSAGE)],
    )

    class Meta:
        model = RecipeIngredient
        fields = (
            'id', 'name', 'measurement_unit', 'amount',)


class RecipeSerializer(ModelSerializer):
    tags = TagSerializer(many=True)
    author = CustomUserSerializer(read_only=True)
    is_favorited = SerializerMethodField()
    ingredients = SerializerMethodField()
    is_in_shopping_cart = SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients', 'is_favorited',
                  'is_in_shopping_cart', 'name', 'image',
                  'text', 'cooking_time',)

    def get_is_favorited(self, obj):
        user = self.context.get('request').user
        return not user.is_anonymous and Favorite.objects.filter(
            user=user, recipe=obj).exists()

    def get_ingredients(self, obj):
        ingredients = RecipeIngredient.objects.filter(recipe=obj)
        serializer = RecipeIngredientSerializer(ingredients, many=True)

        return serializer.data

    def get_is_in_shopping_cart(self, obj):
        user = self.context.get('request').user
        return not user.is_anonymous and ShoppingCart.objects.filter(
            user=user, recipe=obj).exists()


class CreateUpdateRecipeSerializer(ModelSerializer):
    ingredients = RecipeIngredientSerializer(many=True)
    tags = PrimaryKeyRelatedField(queryset=Tag.objects.all(), many=True)
    author = CustomUserSerializer(read_only=True)
    image = Base64ImageField()
    cooking_time = IntegerField(
        validators=[MinValueValidator(
            1, message=INVALID_COOKING_TIME_MESSAGE)])

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients',
            'name', 'image', 'text', 'cooking_time',
        )

    def validate_tags(self, value):
        if not value:
            raise ValidationError(MISSING_TAG_MESSAGE)
        if len(set(value)) != len(value):
            raise ValidationError(DUPLICATE_TAGS_MESSAGE)
        return value

    def validate_ingredients(self, value):
        if not value:
            raise ValidationError(MISSING_INGREDIENT_MESSAGE)

        ingredients_set = set()
        for ingredient_data in value:
            ingredient_id = ingredient_data['id']
            if ingredient_id in ingredients_set:
                raise ValidationError(DUPLICATE_INGREDIENT_MESSAGE)
            ingredients_set.add(ingredient_id)

        return value

    def create_ingredients(self, recipe, ingredients_data):
        ingredients = []
        for ingredient_data in ingredients_data:
            ingredient_id = ingredient_data['id']
            amount = ingredient_data['amount']
            ingredient_obj = get_object_or_404(Ingredient, pk=ingredient_id)
            ingredients.append(RecipeIngredient(
                recipe=recipe, ingredient=ingredient_obj, amount=amount))
        RecipeIngredient.objects.bulk_create(ingredients)

    def create(self, validated_data):
        author = self.context['request'].user
        tags = validated_data.pop('tags')
        ingredients_data = validated_data.pop('ingredients')

        recipe = Recipe.objects.create(author=author, **validated_data)
        recipe.tags.set(tags)
        self.create_ingredients(recipe, ingredients_data)
        return recipe

    def update(self, instance, validated_data):
        tags = validated_data.pop('tags', None)
        if tags is not None:
            instance.tags.set(tags)

        ingredients_data = validated_data.pop('ingredients', None)
        if ingredients_data is not None:
            instance.ingredients.clear()
            self.create_ingredients(instance, ingredients_data)

        return super().update(instance, validated_data)

    def to_representation(self, instance):
        serializer = RecipeSerializer(
            instance,
            context={'request': self.context.get('request')}
        )
        return serializer.data
