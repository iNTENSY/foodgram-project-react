from django_filters import filters
from django_filters.rest_framework import FilterSet

from recipes.models import Ingredient, Recipe


class IngredientFilter(FilterSet):
    name = filters.CharFilter(lookup_expr='startswith')

    class Meta:
        model = Ingredient
        fields = ['name']


class RecipeFilter(FilterSet):
    tags = filters.AllValuesMultipleFilter(
        field_name='tags__slug'
    )
    is_favorited = filters.BooleanFilter(method='get_is_favorited')
    is_in_shopping_cart = filters.BooleanFilter(
        method='get_is_in_shopping_cart'
    )
    author = filters.NumberFilter(field_name='author__id')

    class Meta:
        model = Recipe
        fields = ['tags', 'author']

    def get_is_favorited(self, queryset, name, value):
        user = self.request.user
        if value:
            return Recipe.objects.filter(favourite_recipes__user=user)
        return Recipe.objects.all()

    def get_is_in_shopping_cart(self, queryset, name, value):
        user = self.request.user
        if value:
            return Recipe.objects.shopping_carts(user=user)
        return Recipe.objects.all()
