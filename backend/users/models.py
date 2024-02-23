from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """
    Модель пользователя. Основным параметром является
    использование электронной почты в качестве ключевого идентификатора.
    """
    email = models.EmailField(verbose_name='Электронная почта',
                              unique=True, max_length=255)
    first_name = models.CharField(_('first name'), max_length=150)
    last_name = models.CharField(_('last name'), max_length=150)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self) -> str:
        return (f'{self.first_name[0]}.{self.last_name[0]}. '
                f'[{self.email}]')


class Follow(models.Model):
    """
    Модель отслеживаемых пользователей. Включает в себя
    автора, за кем следят, и самого подписчика.
    """
    author = models.ForeignKey(verbose_name='Автор', to='User',
                               on_delete=models.CASCADE,
                               related_name='subscribers')
    subscriber = models.ForeignKey(verbose_name='Пользователь',
                                   to='User', on_delete=models.CASCADE,
                                   related_name='follows')

    class Meta:
        verbose_name = 'Подписка на пользователя'
        verbose_name_plural = 'Подписки на пользователя'
        ordering = ['-id']
        constraints = [
            models.UniqueConstraint(
                fields=['author', 'subscriber'], name='unique_follow'
            )
        ]

    def __str__(self) -> str:
        return (f'Пользователь "{self.subscriber.email}" '
                f'отслеживает {self.author.username}')
