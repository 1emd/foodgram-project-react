from recipes.models import RecipeIngredient


def process_shopping_cart_items(shopping_cart_items):
    buy_list = {}
    for item in shopping_cart_items:
        ingredients = RecipeIngredient.objects.filter(recipe=item.recipe)
        for ingredient in ingredients:
            key = (
                f'{ingredient.ingredient.name} '
                f'({ingredient.ingredient.measurement_unit})'
            )
            if key in buy_list:
                buy_list[key] += ingredient.amount
            else:
                buy_list[key] = ingredient.amount
    return buy_list
