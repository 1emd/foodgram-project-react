from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api.views import (IngredientViewSet, TagViewSet,
                       RecipeViewSet, CustomUserViewSet)

app_name = 'api'

v1_router = DefaultRouter()
v1_router.register('ingredients', IngredientViewSet, basename='ingredients')
v1_router.register('tags', TagViewSet, basename='tags')
v1_router.register('recipes', RecipeViewSet, basename='recipes')
# v1_router.register(r'titles/(?P<title_id>\d+)/reviews',
#                    ReviewViewSet, basename='reviews')
# v1_router.register(
#     r'titles/(?P<title_id>\d+)/reviews/(?P<review_id>\d+)/comments',
#     CommentViewSet, basename='comments')
v1_router.register('users', CustomUserViewSet, basename='users')

# v1_auth_urlpatterns = [
#     path('auth/signup/', registration, name='signup'),
#     path('auth/token/', get_token, name='token'),
# ]

urlpatterns = [
    path('api/', include(v1_router.urls)),
    path('api/auth/', include('djoser.urls.authtoken'))
    # path('api/', include(v1_auth_urlpatterns)),
]
