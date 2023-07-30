from django_filters.rest_framework import CharFilter, FilterSet, BooleanFilter
from django.db.models import Q
from recipes.models import Ingredient, Recipe


class IngredientFilter(FilterSet):
    name = CharFilter(lookup_expr='icontains')  # lookup_expr='startswith'

    class Meta:
        model = Ingredient
        fields = ['name']


class RecipeFilter(FilterSet):
    is_favourite = BooleanFilter(
        field_name='favourite__user',
        method='filter_by_favourite',
        label='Избранное'
    )
    is_in_shopping_list = BooleanFilter(
        field_name='shoppinglist__user',
        method='filter_by_shopping_list',
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
        fields = ['is_favourite', 'is_in_shopping_list', 'author', 'tags']

    def filter_by_favourite(self, queryset, name, value):
        if value:
            return queryset.filter(favourite__user=self.request.user)
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
