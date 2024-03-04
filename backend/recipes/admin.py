from django.contrib import admin
from recipes.models import (FavoriteRecipe, Ingredient, Recipe,
                            RecipeIngredient, ShoppingCart, Tag)


class RecipeIngredientsInline(admin.TabularInline):
    model = RecipeIngredient


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author', 'counts')
    list_filter = ('name', 'author', 'tags',)
    inlines = (RecipeIngredientsInline,)
    ordering = ['-created_at']

    def counts(self, obj):
        return obj.favorite_recipes.count()


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'color')


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    list_filter = ('name',)


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = ('admin_title', 'ingredient', 'recipe')

    def admin_title(self, obj):
        return f'Запись номер №{obj.id}'

    admin_title.short_description = "Идентификатор"


@admin.register(FavoriteRecipe)
class FavouriteRecipeAdmin(admin.ModelAdmin):
    pass


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('admin_title', 'user', 'recipe')
    list_filter = ('user', 'recipe')

    def admin_title(self, obj):
        return f'Запись на покупку номер {obj.id}'

    admin_title.short_description = "Идентификатор покупки"
