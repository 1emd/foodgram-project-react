from django.contrib import admin

from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)


class RecipeInline(admin.TabularInline):
    model = Recipe.ingredients.through
    extra = 1
    min_num = 1


class RecipeTagsInLine(admin.TabularInline):
    model = Recipe.tags.through
    extra = 1
    min_num = 1


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'measurement_unit')
    list_filter = ('name',)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'color', 'slug')
    list_filter = ('name',)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    inlines = (RecipeInline, RecipeTagsInLine, )
    list_display = ('id', 'name', 'author', 'display_ingredients',
                    'cooking_time', 'display_favorite_count')
    list_filter = ('name', 'author', 'tags__name')
    search_fields = ('name', 'author__username', 'author__email')
    readonly_fields = ('display_favorite_count',)

    @admin.display(description='Число добавлений в избранное')
    def display_favorite_count(self, obj):
        return obj.favorites.count()

    @admin.display(description='Ингредиенты')
    def display_ingredients(self, obj):
        ingredients = obj.ingredients.all()
        ingredient_names = [ingredient.name for ingredient in ingredients]
        return ', '.join(ingredient_names)


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'recipe', 'ingredient', 'amount')
    list_filter = ('recipe', 'ingredient')


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'recipe')
    list_filter = ('user', 'recipe')


@admin.register(ShoppingCart)
class ShoppingListAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'recipe')
    list_filter = ('user', 'recipe')
