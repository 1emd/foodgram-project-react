from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import (GenericViewSet, ModelViewSet,
                                     ReadOnlyModelViewSet)

from api.filters import IngredientFilter, RecipeFilter
from api.pagination import CustomPagination
from api.permissions import (IsAuthorOrAdminOrReadOnly,
                             IsRecipeOwnerOrAuthenticated)
from api.serializers import (CreateUpdateRecipeSerializer,
                             CustomUserCreateSerializer, CustomUserSerializer,
                             IngredientSerializer, RecipeSerializer,
                             SubscriptionSerializer, TagSerializer)
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingList, Tag)
from users.models import Subscription, User

RECIPE_ADDED_TO_FAVORITES = 'Рецепт добавлен в избранное.'
RECIPE_ALREADY_IN_FAVORITES = 'Рецепт уже в избранном.'
RECIPE_REMOVED_FROM_FAVORITES = 'Рецепт удален из избранного.'
RECIPE_NOT_IN_FAVORITES = 'Рецепта нет в избранном.'
RECIPE_ADDED_TO_SHOPPING_LIST = 'Рецепт добавлен в список покупок.'
RECIPE_ALREADY_IN_SHOPPING_LIST = 'Рецепт уже в списке покупок.'
RECIPE_REMOVED_FROM_SHOPPING_LIST = 'Рецепт удален из списка покупок.'
RECIPE_NOT_IN_SHOPPING_LIST = 'Рецепта нет в списке покупок.'
UNAUTHORIZED_USER = 'Пользователь не авторизован.'
SELF_SUBSCRIBE_UNSUBSCRIBE_ERROR = ('Невозможно подписаться или '
                                    'отписаться от самого себя.')
ALREADY_SUBSCRIBED_ERROR = 'Вы уже подписаны на этого автора.'
SUBSCRIPTION_NOT_FOUND_ERROR = ('Вы не подписаны на этого автора, '
                                'либо подписка уже удалена.')
METHOD_NOT_ALLOWED_ERROR = 'Метод не разрешен для данного запроса.'
USER_UNAUTHORIZED_ERROR = 'Пользователь не авторизован.'
INCORRECT_CURRENT_PASSWORD_ERROR = 'Текущий пароль неверен.'
PASSWORD_CHANGE_SUCCESS = 'Пароль успешно изменен.'


class IngredientViewSet(ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    permission_classes = (IsAuthorOrAdminOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter


class TagViewSet(ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    pagination_class = None
    serializer_class = TagSerializer
    permission_classes = (IsAuthorOrAdminOrReadOnly,)


class RecipeViewSet(ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = (IsAuthorOrAdminOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    pagination_class = CustomPagination

    def get_serializer_class(self):
        if self.action in ('create', 'partial_update'):
            return CreateUpdateRecipeSerializer
        return RecipeSerializer

    def perform_create(self, serializer):
        serializer.save()

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=[IsRecipeOwnerOrAuthenticated])
    def favorite(self, request, pk=None):
        recipe = self.get_object()
        user = request.user

        if request.method == 'POST':
            if not Favorite.objects.filter(user=user, recipe=recipe).exists():
                Favorite.objects.create(user=user, recipe=recipe)
                return Response({'message': RECIPE_ADDED_TO_FAVORITES},
                                status=status.HTTP_200_OK)
            return Response({'message': RECIPE_ALREADY_IN_FAVORITES},
                            status=status.HTTP_400_BAD_REQUEST)

        if request.method == 'DELETE':
            if Favorite.objects.filter(user=user, recipe=recipe).exists():
                Favorite.objects.filter(user=user, recipe=recipe).delete()
                return Response({'message': RECIPE_REMOVED_FROM_FAVORITES},
                                status=status.HTTP_200_OK)
            return Response({'message': RECIPE_NOT_IN_FAVORITES},
                            status=status.HTTP_400_BAD_REQUEST)

        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, pk=None):
        recipe = self.get_object()
        user = request.user

        if request.method == 'POST':
            if not ShoppingList.objects.filter(
                    user=user, recipe=recipe).exists():
                ShoppingList.objects.create(user=user, recipe=recipe)
                return Response(
                    {'message': RECIPE_ADDED_TO_SHOPPING_LIST},
                    status=status.HTTP_200_OK
                )
            return Response(
                {'message': RECIPE_ALREADY_IN_SHOPPING_LIST},
                status=status.HTTP_400_BAD_REQUEST
            )

        if request.method == 'DELETE':
            if ShoppingList.objects.filter(user=user, recipe=recipe).exists():
                ShoppingList.objects.filter(user=user, recipe=recipe).delete()
                return Response(
                    {'message': RECIPE_REMOVED_FROM_SHOPPING_LIST},
                    status=status.HTTP_200_OK
                )
            return Response(
                {'message': RECIPE_NOT_IN_SHOPPING_LIST},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @action(detail=False, methods=['get'],
            permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request):
        user = request.user
        shopping_cart_items = ShoppingList.objects.filter(user=user)

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

        content = 'Shopping Cart:\n\n'
        for ingredient, amount in buy_list.items():
            content += f'- {ingredient}: {amount}\n'

        response = HttpResponse(content, content_type='text/plain')
        response[
            'Content-Disposition'] = 'attachment; filename="shopping_cart.txt"'

        return response

    def get_queryset(self):
        queryset = super().get_queryset()

        username = self.request.query_params.get('author')
        if username:
            queryset = queryset.filter(author__username=username)

        return queryset


class CustomUserViewSet(GenericViewSet):
    queryset = User.objects.all()
    pagination_class = CustomPagination

    def get_serializer_class(self):
        if self.action == 'create':
            return CustomUserCreateSerializer
        elif self.action == 'subscriptions':
            return SubscriptionSerializer
        return CustomUserSerializer

    @action(
        detail=False,
        methods=['get'],
        serializer_class=SubscriptionSerializer,
        permission_classes=(IsAuthenticated, )
    )
    def subscriptions(self, request):
        user = request.user
        user_subscriptions = Subscription.objects.filter(user=user)
        author_ids = user_subscriptions.values_list('author_id', flat=True)
        queryset = User.objects.filter(pk__in=author_ids)
        paginated_queryset = self.paginate_queryset(queryset)
        serializer = self.get_serializer(paginated_queryset, many=True)
        return self.get_paginated_response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if not request.user.is_authenticated:
            raise PermissionDenied(
                detail=UNAUTHORIZED_USER,
                code=status.HTTP_401_UNAUTHORIZED)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='me', url_name='me')
    def my_profile(self, request):
        if request.user.is_authenticated:
            serializer = self.get_serializer(request.user)
            return Response(serializer.data)
        else:
            return Response({'detail': UNAUTHORIZED_USER}, status=401)

    @action(
        detail=True,
        methods=['post', 'delete'],
        serializer_class=SubscriptionSerializer,
        permission_classes=[IsAuthenticated]
    )
    def subscribe(self, request, pk=None):
        user = request.user
        author = get_object_or_404(User, pk=pk)

        if user == author:
            return Response({'message': SELF_SUBSCRIBE_UNSUBSCRIBE_ERROR},
                            status=status.HTTP_400_BAD_REQUEST)

        subscription_exists = Subscription.objects.filter(
            user=user, author=author).exists()

        if request.method == 'POST':
            if subscription_exists:
                return Response({'message': ALREADY_SUBSCRIBED_ERROR},
                                status=status.HTTP_400_BAD_REQUEST)

            Subscription.objects.create(user=user, author=author)
            serializer = SubscriptionSerializer(
                author, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif request.method == 'DELETE':
            if not subscription_exists:
                return Response({'message': SUBSCRIPTION_NOT_FOUND_ERROR},
                                status=status.HTTP_400_BAD_REQUEST)

            Subscription.objects.filter(user=user, author=author).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response({'message': METHOD_NOT_ALLOWED_ERROR},
                        status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @action(detail=False, methods=['post'])
    def set_password(self, request):
        current_password = request.data.get('current_password')
        new_password = request.data.get('new_password')

        if not request.user.is_authenticated:
            raise PermissionDenied(
                detail=USER_UNAUTHORIZED_ERROR,
                code=status.HTTP_401_UNAUTHORIZED)

        if not request.user.check_password(current_password):
            raise ValidationError(
                {'current_password': [INCORRECT_CURRENT_PASSWORD_ERROR]})

        request.user.set_password(new_password)
        request.user.save()

        return Response({'detail': PASSWORD_CHANGE_SUCCESS},
                        status=status.HTTP_200_OK)
