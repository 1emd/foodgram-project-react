# from django.shortcuts import render
# from rest_framework.renderers import StaticHTMLRenderer
from django.http import HttpResponse
# from djoser.views import UserViewSet
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet, GenericViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from recipes.models import (Ingredient, Tag, Recipe,
                            Favourite, ShoppingList, RecipeIngredient,)
from users.models import User, Subscription
from api.serializers import (IngredientSerializer, TagSerializer,
                             RecipeIngredientSerializer,
                             RecipeCreateUpdateSerializer, RecipeSerializer,
                             UserCreateSerializer, UserProfileSerializer,
                             SubscriptionSerializer, UserWithRecipesSerializer,
                             CustomUserCreateSerializer, CustomUserSerializer)
from api.permissions import IsAuthorOrAdminOrReadOnly
from api.filters import IngredientFilter, RecipeFilter
from api.pagination import CustomPagination


class IngredientViewSet(ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (IsAuthorOrAdminOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter


class TagViewSet(ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
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
            return RecipeCreateUpdateSerializer
        return RecipeSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=True, methods=['post', 'delete'])
    def favorite(self, request, pk=None):
        recipe = self.get_object()
        user = request.user

        if request.method == 'POST':
            if not Favourite.objects.filter(user=user, recipe=recipe).exists():
                Favourite.objects.create(user=user, recipe=recipe)
                return Response({'message': 'Рецепт добавлен в избранное.'},
                                status=status.HTTP_200_OK)
            return Response({'message': 'Рецепт уже в избранном.'},
                            status=status.HTTP_400_BAD_REQUEST)

        if request.method == 'DELETE':
            if Favourite.objects.filter(user=user, recipe=recipe).exists():
                Favourite.objects.filter(user=user, recipe=recipe).delete()
                return Response({'message': 'Рецепт удален из избранного.'},
                                status=status.HTTP_200_OK)
            return Response({'message': 'Рецепта нет в избранном.'},
                            status=status.HTTP_400_BAD_REQUEST)

        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @action(detail=True, methods=['post', 'delete'])
    def shopping_list(self, request, pk=None):
        recipe = self.get_object()
        user = request.user

        if request.method == 'POST':
            if not ShoppingList.objects.filter(
                    user=user, recipe=recipe).exists():
                ShoppingList.objects.create(user=user, recipe=recipe)
                return Response(
                    {'message': 'Рецепт добавлен в список покупок.'},
                    status=status.HTTP_200_OK
                )
            return Response(
                {'message': 'Рецепт уже в списке покупок.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if request.method == 'DELETE':
            if ShoppingList.objects.filter(user=user, recipe=recipe).exists():
                ShoppingList.objects.filter(user=user, recipe=recipe).delete()
                return Response(
                    {'message': 'Рецепт удален из списка покупок.'},
                    status=status.HTTP_200_OK
                )
            return Response(
                {'message': 'Рецепта нет в списке покупок.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @action(detail=False, methods=['get'])
    def download_shopping_list(self, request):
        user = request.user
        shopping_list_items = ShoppingList.objects.filter(user=user)

        # Суммируем перечень ингредиентов и удаляем дубликаты
        buy_list = {}
        for item in shopping_list_items:
            ingredients = RecipeIngredient.objects.filter(recipe=item.recipe)
            for ingredient in ingredients:
                key = (
                    f'{ingredient.ingredient.name} '
                    f'({ingredient.ingredient.measurement_unit})'
                )
                # key = f"{ingredient.ingredient.name} ({ingredient.ingredient.measurement_unit})"
                if key in buy_list:
                    buy_list[key] += ingredient.amount
                else:
                    buy_list[key] = ingredient.amount

        # Сериализуем и возвращаем список покупок
        # serializer = RecipeIngredientSerializer([
        #     {'ingredient': key.split(
        #         ' (')[0], 'amount': value, 'measurement_unit': key.split(
        #             ' (')[1][:-1]}
        #     for key, value in buy_list.items()
        # ], many=True)
        # return Response(serializer.data, status=status.HTTP_200_OK)

        # Создаем текстовый файл с содержимым списка покупок
        content = "Shopping List:\n\n"
        for ingredient, amount in buy_list.items():
            content += f"- {ingredient}: {amount}\n"

        # Возвращаем текстовый файл в качестве ответа
        response = HttpResponse(content, content_type='text/plain')
        response[
            'Content-Disposition'] = 'attachment; filename="shopping_list.txt"'

        return response

    def get_queryset(self):
        queryset = super().get_queryset()

        # Применяем фильтрацию по пользователю, если выбран пользователь
        username = self.request.query_params.get('author')
        if username:
            queryset = queryset.filter(author__username=username)

        return queryset


class CustomUserViewSet(GenericViewSet):
    queryset = User.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return CustomUserCreateSerializer
        elif self.action in ['list', 'retrieve', 'update', 'partial_update']:
            return CustomUserSerializer
        elif self.action == 'subscriptions':
            return SubscriptionSerializer
        return UserCreateSerializer

    @action(
        detail=False, methods=['get'],
        serializer_class=SubscriptionSerializer
    )
    def subscriptions(self, request):
        user = self.request.user
        user_subscriptions = user.subscriber.all()
        authors = [item.author.id for item in user_subscriptions]
        queryset = User.objects.filter(pk__in=authors)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = SubscriptionSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = SubscriptionSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def my_profile(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def recipes(self, request, pk=None):
        user = self.get_object()
        recipes = user.recipes.all()
        serializer = RecipeSerializer(recipes, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def my_subscriptions(self, request):
        queryset = Subscription.objects.filter(user=request.user)
        serializer = UserWithRecipesSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def subscribe(self, request):
        serializer = SubscriptionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'])
    def unsubscribe(self, request):
        queryset = Subscription.objects.filter(user=request.user)
        author_id = request.data.get('author_id')
        subscription = queryset.filter(author_id=author_id).first()
        if subscription:
            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {'error': 'Subscription not found.'},
            status=status.HTTP_400_BAD_REQUEST)
