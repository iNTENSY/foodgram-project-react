from django.contrib.auth import get_user_model
from django.db import transaction
from django.shortcuts import get_object_or_404
from djoser.serializers import UserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from recipes.models import Ingredient, Recipe, RecipeIngredient, Tag
from users.serializers import CustomUserSerializer

User = get_user_model()


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class FullInfoIngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = '__all__'


class IngredientSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()
    name = serializers.CharField(read_only=True, source='ingredient.name')
    measurement_unit = serializers.CharField(
        read_only=True, source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeReadSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    tags = TagSerializer(read_only=True, many=True)
    image = Base64ImageField()
    ingredients = FullInfoIngredientSerializer(read_only=True, many=True)
    is_favorited = serializers.SerializerMethodField(read_only=True)
    is_in_shopping_cart = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients',
                  'name', 'image', 'text', 'cooking_time',
                  'is_favorited', 'is_in_shopping_cart')

    def get_is_favorited(self, obj):
        user = self.context['request'].user
        if user.is_anonymous:
            return False
        return obj.favorite_recipes.filter(recipe=obj, user=user).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self.context['request'].user
        if user.is_anonymous:
            return False
        return obj.shopping_carts.filter(recipe=obj, user=user).exists()


class IngredientInRecipeWriteSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(write_only=True)

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class RecipeCreateSerializer(serializers.ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(queryset=Tag.objects.all(),
                                              many=True)
    author = CustomUserSerializer(read_only=True)
    ingredients = IngredientInRecipeWriteSerializer(many=True)
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients',
                  'name', 'image', 'text', 'cooking_time')

    def validate_ingredients(self, value):
        ingredients = value
        if not ingredients:
            raise ValidationError(
                detail={'ingredients': 'Требуется хотя бы один ингредиент'}
            )
        ingredient_list = []
        for item in ingredients:
            item_object = get_object_or_404(Ingredient, id=item['id'])
            if item_object in ingredient_list:
                raise ValidationError(
                    detail={
                        'ingredients': 'Ингредиенты не должны повторяться'
                    }
                )
            if int(item['amount']) <= 0:
                raise ValidationError(
                    detail={
                        'ingredients': 'Количество должно быть больше 0'
                    }
                )
            ingredient_list.append(item_object)
        return value

    def validate_tags(self, value):
        tags = value
        if not tags:
            raise ValidationError(
                detail={
                    'tags': 'Требуется хотя бы один тег'
                }
            )
        tags_list = []
        for item in tags:
            if item in tags_list:
                raise ValidationError(
                    detail={'tags': 'Тег не должен повторяться'}
                )
            tags_list.append(item)
        return value

    @transaction.atomic
    def create_ingredients(self, recipe, ingredients):
        all_ingredients = [
            RecipeIngredient(
                amount=ingredient['amount'],
                recipe=recipe,
                ingredient=Ingredient.objects.get(id=ingredient['id'])
            )
            for ingredient in ingredients
        ]
        RecipeIngredient.objects.bulk_create(all_ingredients)

    @transaction.atomic
    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        self.create_ingredients(recipe=recipe, ingredients=ingredients)
        return recipe

    #@transaction.atomic
    #def update(self, instance, validated_data):
    #    tags = validated_data.pop('tags')
    #    ingredients = validated_data.pop('ingredients')
    #    instance = super().update(instance, validated_data)
    #    instance.tags.clear()
    #    instance.tags.set(tags)
    #    instance.ingredients.clear()
    #    self.create_ingredients(recipe=instance, ingredients=ingredients)
    #    instance.save()
    #    return instance

    def to_representation(self, instance):
        request = self.context.get('request')
        context = {'request': request}
        return RecipeReadSerializer(instance, context=context).data


class RecipeShortInfoSerializer(serializers.ModelSerializer):
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'image', 'name', 'cooking_time')
