from django.db.models import Q
from django_filters.rest_framework import BooleanFilter, CharFilter, FilterSet

from recipes.models import Ingredient, Recipe


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
        field_name='shoppingcart__user',
        method='filter_by_shopping_cart',
        label='Список покупок'
    )
    author = CharFilter(
        field_name='author__username',
        lookup_expr='iexact',
        label='Автор'
    )
    tags = CharFilter(
        method='filter_by_tags',
        label='Теги (через запятую)'
    )

    class Meta:
        model = Recipe
        fields = ('is_favorite', 'is_in_shopping_cart', 'author', 'tags',)

    def filter_by_favorite(self, queryset, name, value):
        if value:
            return queryset.filter(favorite__user=self.request.user)
        return queryset

    def filter_by_shopping_cart(self, queryset, name, value):
        if value:
            return queryset.filter(shoppingcart__user=self.request.user)
        return queryset

    def filter_by_tags(self, queryset, name, value):
        tags = value.split(',')
        filters = Q()
        for tag in tags:
            filters |= Q(tags__slug__iexact=tag.strip())

        return queryset.filter(filters)
