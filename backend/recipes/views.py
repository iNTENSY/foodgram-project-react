from django.shortcuts import render
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets

from recipes.models import Tag, Ingredient, Recipe
from recipes import serializers, filters, permissions


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = serializers.TagSerializer


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = serializers.IngredientSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = filters.IngredientFilter


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = serializers.RecipeReadSerializer
    permission_classes = (permissions.IsAdminOrReadOnly,
                          permissions.IsAuthorOrReadOnly)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = filters.RecipeFilter

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
