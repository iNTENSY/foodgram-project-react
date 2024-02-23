import datetime as dt

from http import HTTPStatus
from typing import Type

from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, SAFE_METHODS
from rest_framework.decorators import action
from rest_framework.response import Response

from recipes.models import Tag, Ingredient, Recipe, ShoppingCart, FavoriteRecipe, RecipeIngredient
from recipes import serializers, filters
from recipes.paginations import CustomPagination
from recipes.permissions import IsAuthorOrReadOnly, IsAdminOrReadOnly
from recipes.serializers import RecipeShortInfoSerializer

User = get_user_model()


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = serializers.TagSerializer
    permission_classes = (IsAdminOrReadOnly,)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    permission_classes = (IsAdminOrReadOnly,)
    serializer_class = serializers.FullInfoIngredientSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = filters.IngredientFilter


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = (IsAdminOrReadOnly | IsAuthorOrReadOnly)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = filters.RecipeFilter
    pagination_class = CustomPagination

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return serializers.RecipeReadSerializer
        return serializers.RecipeCreateSerializer

    @action(
        methods=['POST', 'DELETE'],
        detail=True,
        permission_classes=(IsAuthenticated,)
    )
    def shopping_cart(self, *args, **kwargs):
        user = self.request.user
        if self.request.method == 'POST':
            return self.add_to(ShoppingCart, user, self.kwargs['pk'])
        else:
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
        else:
            return self.delete_from(FavoriteRecipe, user, self.kwargs['pk'])

    @action(
        methods=['GET'],
        detail=False,
        permission_classes=(IsAuthenticated,)
    )
    def download_shopping_cart(self, request, *args, **kwargs):
        user = request.user
        if not user.shopping_cart.exists():
            return Response(status=HTTPStatus.NOT_FOUND)
        ingredients = RecipeIngredient.objects.filter(
            recipe__shopping_carts__user=user
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
    def add_to(model: Type[ShoppingCart | FavoriteRecipe], user: User, pk: int):
        if model.objects.filter(recipe_id=pk, user=user).exists():
            return Response({'errors': 'Рецепт уже был добавлен'}, status=HTTPStatus.BAD_REQUEST)
        recipe = get_object_or_404(Recipe, id=pk)
        model.objects.create(recipe=recipe, user=user)
        serializer = RecipeShortInfoSerializer(recipe)
        return Response(serializer.data, status=HTTPStatus.CREATED)

    @staticmethod
    def delete_from(model: Type[ShoppingCart | FavoriteRecipe], user: User, pk: int):
        obj = model.objects.filter(recipe_id=pk, user=user)
        if obj.exists():
            obj.delete()
            return Response(status=HTTPStatus.NO_CONTENT)
        return Response({'error': 'Рецепт не существует или был удален'}, status=HTTPStatus.BAD_REQUEST)
