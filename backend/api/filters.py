from django_filters.rest_framework import (BooleanFilter, CharFilter,
                                           FilterSet,
                                           ModelMultipleChoiceFilter)

from recipes.models import Ingredient, Recipe, Tag


class IngredientFilter(FilterSet):
    name = CharFilter(lookup_expr='icontains')

    class Meta:
        model = Ingredient
        fields = ('name',)


class RecipeFilter(FilterSet):
    is_favorite = BooleanFilter(
        field_name='favorite__user',
        method='filter_by_favorite',
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

    class Meta:
        model = Recipe
        fields = ('is_favorite', 'is_in_shopping_cart',
                  'tags', 'author__username',)

    def filter_by_favorite(self, queryset, name, value):
        user = self.request.user
        if value and user.is_authenticated:
            return queryset.filter(favorites__user=user)
        return queryset

    def filter_by_shopping_cart(self, queryset, name, value):
        user = self.request.user
        if value and user.is_authenticated:
            return queryset.filter(shopping_cart__user=user)
        return queryset
