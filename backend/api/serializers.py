import base64
from django.core.validators import MinValueValidator
from rest_framework.validators import UniqueTogetherValidator
from rest_framework.serializers import (
    ModelSerializer, SerializerMethodField,
    IntegerField, ImageField, CharField)
from rest_framework.exceptions import ValidationError
from rest_framework.relations import PrimaryKeyRelatedField
from django.core.files.base import ContentFile

from recipes.models import (
    Ingredient, Tag, Favourite, ShoppingList, RecipeIngredient, Recipe)
from users.models import User, Subscription


class CustomUserCreateSerializer(ModelSerializer):
    password = CharField(write_only=True)

    class Meta:
        model = User
        fields = ('email', 'username', 'first_name', 'last_name', 'password')

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user


class CustomUserSerializer(ModelSerializer):
    is_subscribed = SerializerMethodField()

    def get_is_subscribed(self, obj):
        user = self.context['request'].user

        if user.is_anonymous:
            return False

        return Subscription.objects.filter(user=user, author=obj).exists()

    class Meta:
        model = User
        fields = ('id', 'username', 'first_name',
                  'last_name', 'email', 'is_subscribed')


class UserCreateSerializer(ModelSerializer):
    password = CharField(write_only=True)

    class Meta:
        model = User
        fields = ('email', 'username', 'first_name', 'last_name', 'password')
        extra_kwargs = {
            'password': {'write_only': True},
        }

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user


class UserProfileSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'first_name', 'last_name')


class SubscriptionSerializer(ModelSerializer):
    class Meta:
        model = Subscription
        fields = ('author',)


class RecipeMinifiedSerializer(ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'title', 'image')


class UserWithRecipesSerializer(ModelSerializer):
    recipes = RecipeMinifiedSerializer(many=True, source='author.recipes')

    class Meta:
        model = User
        fields = ('id', 'email', 'username',
                  'first_name', 'last_name', 'recipes')


class IngredientSerializer(ModelSerializer):

    class Meta:
        model = Ingredient
        fields = '__all__'


class TagSerializer(ModelSerializer):

    class Meta:
        model = Tag
        fields = '__all__'


# class FavouriteSerializer(serializers.ModelSerializer):

#    class Meta:
#        model = Favourite
#        fields = '__all__'

class Base64ImageField(ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]

            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class RecipeIngredientSerializer(ModelSerializer):
    id = SerializerMethodField(method_name='get_id')
    name = SerializerMethodField(method_name='get_name')
    measurement_unit = SerializerMethodField(
        method_name='get_measurement_unit'
    )
    amount = IntegerField(min_value=1, validators=[
        UniqueTogetherValidator(
            queryset=RecipeIngredient.objects.all(), fields=(
                'recipe', 'ingredient'))
    ])

    def get_id(self, obj):
        return obj.ingredient.id

    def get_name(self, obj):
        return obj.ingredient.name

    def get_measurement_unit(self, obj):
        return obj.ingredient.measurement_unit


class RecipeSerializer(ModelSerializer):
    author = CustomUserSerializer(read_only=True)
    tags = TagSerializer(many=True)
    ingredients = RecipeIngredientSerializer(many=True)
    is_favorited = SerializerMethodField()
    is_in_shopping_list = SerializerMethodField()

    def get_is_favorited(self, obj):
        user = self.context.get('request').user
        return not user.is_anonymous and Favourite.objects.filter(
            user=user, recipe=obj).exists()

    def get_ingredients(self, obj):
        ingredients = RecipeIngredient.objects.filter(recipe=obj)
        serializer = RecipeIngredientSerializer(ingredients, many=True)

        return serializer.data

    def get_is_in_shopping_list(self, obj):
        user = self.context.get('request').user
        return not user.is_anonymous and ShoppingList.objects.filter(
            user=user, recipe=obj).exists()

    class Meta:
        model = Recipe
        fields = ('id', 'author', 'title', 'image',
                  'description', 'ingredients', 'tags',
                  'cooking_time', 'is_favorited', 'is_in_shopping_cart')


class RecipeCreateUpdateSerializer(ModelSerializer):
    author = CustomUserSerializer(read_only=True)
    tags = PrimaryKeyRelatedField(queryset=Tag.objects.all(), many=True)
    ingredients = RecipeIngredientSerializer(many=True)
    image = ImageField(
        max_length=None, use_url=True, required=False)
    cooking_time = IntegerField(validators=[MinValueValidator(1)])

    def validate_tags(self, value):
        if not value:
            raise ValidationError('Нужно добавить хотя бы один тег.')
        return value

    def validate_ingredients(self, value):
        if not value:
            raise ValidationError('Нужно добавить хотя бы один ингредиент.')

        ingredients_set = set()
        for ingredient in value:
            ingredient_id = ingredient['ingredient'].id
            if ingredient_id in ingredients_set:
                raise ValidationError(
                    'У рецепта не может быть два одинаковых ингредиента.')
            ingredients_set.add(ingredient_id)

        return value

    def create(self, validated_data):
        author = self.context['request'].user
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')

        recipe = Recipe.objects.create(author=author, **validated_data)
        recipe.tags.set(tags)

        for ingredient in ingredients:
            amount = ingredient['amount']
            ingredient_obj = ingredient['ingredient']
            RecipeIngredient.objects.create(
                recipe=recipe, ingredient=ingredient_obj, amount=amount)

        return recipe

    def update(self, instance, validated_data):
        tags = validated_data.pop('tags', None)
        if tags is not None:
            instance.tags.set(tags)

        ingredients = validated_data.pop('ingredients', None)
        if ingredients is not None:
            instance.ingredients.clear()
            for ingredient in ingredients:
                amount = ingredient['amount']
                ingredient_obj = ingredient['ingredient']
                RecipeIngredient.objects.update_or_create(
                    recipe=instance,
                    ingredient=ingredient_obj,
                    defaults={'amount': amount}
                )

        return super().update(instance, validated_data)

    class Meta:
        model = Recipe
        exclude = ('pub_date',)

    def to_representation(self, instance):
        serializer = RecipeSerializer(
            instance,
            context={'request': self.context.get('request')}
        )
        return serializer.data
