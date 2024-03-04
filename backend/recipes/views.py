import datetime as dt
from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.db.models import Prefetch, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from recipes import filters, serializers
from recipes.filters import RecipeFilter
from recipes.models import (FavoriteRecipe, Ingredient, Recipe,
                            RecipeIngredient, ShoppingCart, Tag)
from recipes.paginations import CustomPagination
from recipes.permissions import IsAdminOrReadOnly, IsAuthorOrReadOnlyPermission
from recipes.serializers import (ReadRecipeSerializer, RecipeCreateSerializer,
                                 RecipeShortInfoSerializer)
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (SAFE_METHODS, IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response

User = get_user_model()


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = serializers.TagSerializer
    permission_classes = (IsAdminOrReadOnly,)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    permission_classes = (IsAdminOrReadOnly,)
    serializer_class = serializers.IngredientsSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = filters.IngredientFilter


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = (
        Recipe.objects
        .select_related('author')
        .prefetch_related(Prefetch('ingredients'))
        .all()
    )
    permission_classes = (IsAuthorOrReadOnlyPermission,
                          IsAuthenticatedOrReadOnly)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    pagination_class = CustomPagination

    def get_serializer_context(self):
        context = super().get_serializer_context()
        if self.request.user.is_authenticated:
            context['subscriptions'] = set(
                FavoriteRecipe.objects
                .filter(user=self.request.user)
                .values_list('recipe__author_id', flat=True)
            )
            context['is_in_shopping_cart'] = set(
                ShoppingCart.objects
                .filter(user=self.request.user)
                .values_list('recipe_id', flat=True)
            )
        return context

    def get_queryset(self):
        request = self.request
        user = request.user
        queryset = self.queryset
        is_favorite = request.query_params.get('is_favorited')
        is_in_shopping_cart = request.query_params.get('is_in_shopping_cart')

        if is_favorite:
            queryset = queryset.filter(favorite_recipes__user=user)

        if is_in_shopping_cart:
            queryset = queryset.filter(shopping_carts__user=user)

        return queryset

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return ReadRecipeSerializer
        return RecipeCreateSerializer

    @action(
        methods=['POST', 'DELETE'],
        detail=True,
        permission_classes=(IsAuthenticated,)
    )
    def shopping_cart(self, *args, **kwargs):
        user = self.request.user
        if self.request.method == 'POST':
            return self.add_to(ShoppingCart, user, self.kwargs['pk'])
        return self.delete_from(ShoppingCart, user, self.kwargs['pk'])

    @action(
        methods=['POST', 'DELETE'],
        detail=True,
        permission_classes=(IsAuthenticated,)
    )
    def favorite(self, *args, **kwargs):
        user = self.request.user
        if self.request.method == 'POST':
            return self.add_to(FavoriteRecipe, user, self.kwargs['pk'])
        return self.delete_from(FavoriteRecipe, user, self.kwargs['pk'])

    @action(
        methods=['GET'],
        detail=False,
        permission_classes=(IsAuthenticated,)
    )
    def download_shopping_cart(self, request, *args, **kwargs):
        if not request.user.shopping_cart.exists():
            return Response(status=HTTPStatus.NOT_FOUND)
        ingredients = RecipeIngredient.objects.filter(
            recipe__shopping_carts__user=request.user
        ).values(
            'ingredient__name',
            'ingredient__measurement_unit'
        ).annotate(amount=Sum('amount'))

        today = dt.date.today()
        title = f'Foodgram: {today}\n\n'
        shopping_list = title + '\n'.join(
            [
                f'- {ingredient["ingredient__name"]} '
                f'({ingredient["ingredient__measurement_unit"]})'
                f' - {ingredient["amount"]}'
                for ingredient in ingredients
            ]
        )

        filename = f'{today}-shopping-list.txt'
        response = HttpResponse(shopping_list, content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename={filename}'
        return response

    @staticmethod
    def add_to(model, user, pk: int):
        if model.objects.filter(recipe_id=pk, user=user).exists():
            return Response(
                {'errors': 'Рецепт уже был добавлен'},
                status=HTTPStatus.BAD_REQUEST
            )
        recipe = get_object_or_404(Recipe, id=pk)
        model.objects.create(recipe=recipe, user=user)
        serializer = RecipeShortInfoSerializer(recipe)
        return Response(serializer.data, status=HTTPStatus.CREATED)

    @staticmethod
    def delete_from(model, user: User, pk: int):
        obj = model.objects.filter(recipe_id=pk, user=user)
        if obj.exists():
            obj.delete()
            return Response(status=HTTPStatus.NO_CONTENT)
        return Response(
            {'error': 'Рецепт не существует или был удален'},
            status=HTTPStatus.BAD_REQUEST
        )
