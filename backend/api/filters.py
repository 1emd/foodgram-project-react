from django_filters.rest_framework import (BooleanFilter, CharFilter,
                                           FilterSet,
                                           ModelMultipleChoiceFilter,
                                           NumberFilter)

from recipes.models import Ingredient, Recipe, ShoppingCart, Tag


class IngredientFilter(FilterSet):
    name = CharFilter(lookup_expr='icontains')

    class Meta:
        model = Ingredient
        fields = ('name',)


class RecipeFilter(FilterSet):
    is_favorited = BooleanFilter(
        method='filter_by_favorited',
        label='Избранное'
    )
    is_in_shopping_cart = BooleanFilter(
        field_name='shopping_cart__user',
        method='filter_by_shopping_cart',
        label='Список покупок'
    )
    tags = ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all(),
        label='Теги'
    )
    author = NumberFilter(
        field_name='author',
        label='Автор'
    )

    class Meta:
        model = Recipe
        fields = ('is_favorited', 'is_in_shopping_cart',
                  'tags', 'author',)

    def filter_by_favorited(self, queryset, name, value):
        user = self.request.user
        if user.is_authenticated and value:
            return queryset.filter(favorites__user=user)
        return queryset

    def filter_by_shopping_cart(self, queryset, name, value):
        user = self.request.user
        if value and user.is_authenticated:
            shopping_cart_recipes = ShoppingCart.objects.filter(
                user=user).values('recipe')
            return queryset.filter(id__in=shopping_cart_recipes)
        return queryset
