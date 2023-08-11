from colorfield.fields import ColorField
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from recipes.constants import (MAX_AMOUNT, MAX_COOKING_TIME, MAX_FIELD_LENGTH,
                               MIN_VALUE)
from users.models import User


class Ingredient(models.Model):
    name = models.CharField(
        max_length=MAX_FIELD_LENGTH,
        verbose_name='Название ингредиента',
    )
    measurement_unit = models.CharField(
        max_length=MAX_FIELD_LENGTH,
        verbose_name='Единица измерения',
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        constraints = (
            models.UniqueConstraint(
                fields=('name', 'measurement_unit'),
                name='unique_ingredient_unit'),
        )

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField(
        max_length=MAX_FIELD_LENGTH,
        unique=True,
        verbose_name='Название',
    )
    color = ColorField(
        unique=True,
        verbose_name='Цветовой HEX-код',
    )
    slug = models.SlugField(
        max_length=MAX_FIELD_LENGTH,
        unique=True,
        verbose_name='Slug'
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Recipe(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор публикации',
    )
    name = models.CharField(
        max_length=MAX_FIELD_LENGTH,
        verbose_name='Название рецепта',
    )
    image = models.ImageField(
        upload_to=' recipes/images/',
        null=True,
        default=None,
        verbose_name='Изображение',
    )
    text = models.TextField(
        null=True,
        default=None,
        verbose_name='Описание',
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        related_name='recipes',
        verbose_name='Игредиенты',
    )
    tags = models.ManyToManyField(
        Tag,
        through='RecipeTag',
        related_name='recipes',
        verbose_name='Теги',
    )
    cooking_time = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(
            MIN_VALUE), MaxValueValidator(MAX_COOKING_TIME)],
        verbose_name='Время приготовления в минутах',
    )
    date_created = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )

    class Meta:
        ordering = ('-date_created', )
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Игредиент'
    )
    amount = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(
            MIN_VALUE), MaxValueValidator(MAX_AMOUNT)],
        verbose_name='Количество'
    )

    class Meta:
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецепте'

    def __str__(self):
        return f'Рецепт {self.recipe} содержит {self.ingredient}.'


class RecipeTag(models.Model):
    tag = models.ForeignKey(
        Tag,
        on_delete=models.CASCADE,
        verbose_name='Тег'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )

    class Meta:
        verbose_name = 'Тег рецепта'
        verbose_name_plural = 'Теги рецепта'

    def __str__(self):
        return f'Рецепт {self.recipe} имеет тег {self.tag}'


class CommonFields(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='%(class)ss',
        verbose_name='Пользователь',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='%(class)ss',
        verbose_name='Рецепт',
    )
    added_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата и время добавления'
    )

    class Meta:
        abstract = True
        ordering = ('-added_at', )
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_user_recipe'
            ),
        )

    def __str__(self):
        return (f'Пользователь {self.user} '
                f'добавил рецепт {self.recipe} в {self._meta.verbose_name}.')


class Favorite(CommonFields):

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'


class ShoppingCart(CommonFields):

    class Meta:
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Список покупок'
