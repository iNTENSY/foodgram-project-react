from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import UniqueConstraint

User = get_user_model()


class CreatedAtAbstractModel(models.Model):
    """
    Абстрактная модель, которая используется
    для установления даты создания объекта.
    """
    created_at = models.DateTimeField(verbose_name='Дата создания',
                                      auto_now_add=True)

    class Meta:
        abstract = True


class Tag(models.Model):
    """
    Модель тегов. Все указанные поля должны быть уникальны.
    Цвет подразумевает использование HEX-формата
    """
    name = models.CharField(verbose_name='Название тега',
                            max_length=20, unique=True)
    color = models.CharField(verbose_name='Цвет в HEX-формате',
                             max_length=7, unique=True)
    slug = models.SlugField(verbose_name='Слаг', unique=True,
                            db_index=True, blank=True)

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self) -> str:
        return f'{self.name} (цвет: {self.color})'


class Ingredient(models.Model):
    """
    Модель ингредиентов. Включает в себя название продукта и
    его единицу измерения. Название продукта должно быть уникальным.
    """
    name = models.CharField(verbose_name='Название продукта',
                            max_length=100, unique=True)
    measurement_unit = models.CharField(verbose_name='Единица измерения',
                                        max_length=100)

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ('name',)

    def __str__(self) -> str:
        return str(self.name)


class Recipe(CreatedAtAbstractModel):
    """
    Модель рецептов. Включает в себя название, картинку, описание.
    Поля ингредиентов связана с промежуточной моделью 'RecipeIngredient'.
    Поле тегов напрямую не использует промежуточную таблицу.
    """
    author = models.ForeignKey(verbose_name='Автор рецепта',
                               related_name='recipes', to=User,
                               on_delete=models.CASCADE)
    name = models.CharField(verbose_name='Название рецепта', max_length=200)
    image = models.ImageField(verbose_name='Картинка', upload_to='recipes')
    text = models.TextField(verbose_name='Описание')
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время приготовления',
        validators=[
            MinValueValidator(
                limit_value=1,
                message=('Время приготовления не '
                         'может быть меньше 1 (в минутах)')
            )
        ])
    ingredients = models.ManyToManyField(verbose_name='Ингредиенты',
                                         related_name='recipes',
                                         through='RecipeIngredient',
                                         to='Ingredient')
    tags = models.ManyToManyField(verbose_name='Теги',
                                  related_name='recipes',
                                  to='Tag')

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-created_at',)

    def __str__(self) -> str:
        return str(self.name)


class RecipeIngredient(models.Model):
    """
    Промежуточная таблица, включающая в себя рецепт
    и ингредиент с указанием его количества.
    """
    recipe = models.ForeignKey(verbose_name='Рецепт', to='Recipe',
                               on_delete=models.CASCADE,
                               related_name='recipesingredients')
    ingredient = models.ForeignKey(verbose_name='Ингредиент',
                                   to='Ingredient', on_delete=models.CASCADE)
    amount = models.PositiveSmallIntegerField(
        verbose_name='Количество ингредиента',
        validators=[
            MinValueValidator(
                limit_value=1,
                message=('Количество не может '
                         'быть меньше 1.')
            )
        ])

    class Meta:
        constraints = (
            models.UniqueConstraint(fields=('recipe', 'ingredient',),
                                    name='unique_recipe_with_ingredients'),
        )
        ordering = ['recipe']
        verbose_name = 'Игредиент'
        verbose_name_plural = 'Количество ингридиентов'

    def __str__(self):
        return f'{self.recipe} ингредиенты: {self.ingredient}'


class FavoriteRecipe(CreatedAtAbstractModel):
    """
    Модель избранных рецептов. Включает в себя поле
    пользователя, добавившего рецепт, и сам рецепт.
    """
    user = models.ForeignKey(verbose_name='Пользователь', to=User,
                             on_delete=models.CASCADE,
                             related_name='favorite_recipes')
    recipe = models.ForeignKey(verbose_name='Рецепт', to='Recipe',
                               on_delete=models.CASCADE,
                               related_name='favorite_recipes')

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        constraints = [
            UniqueConstraint(fields=['user', 'recipe'],
                             name='unique_favorite')
        ]

    def __str__(self) -> str:
        return f'{self.user} - [{self.recipe.name}]'


class ShoppingCart(CreatedAtAbstractModel):
    """
    Модель списка рецептов, требуемых к покупке.
    """
    user = models.ForeignKey(verbose_name='Пользователь', to=User,
                             on_delete=models.CASCADE,
                             related_name='shopping_cart')
    recipe = models.ForeignKey(verbose_name='Рецепт', to='Recipe',
                               on_delete=models.CASCADE,
                               related_name='shopping_carts')

    class Meta:
        verbose_name = 'Покупка'
        verbose_name_plural = 'Покупки'
        constraints = [
            UniqueConstraint(fields=['user', 'recipe'],
                             name='unique_shopping_cart')
        ]

    def __str__(self) -> str:
        return (f'[{self.created_at.strftime("%d.%m.%Y %H:%M")}] '
                f'{self.user}: {self.recipe.name}')
