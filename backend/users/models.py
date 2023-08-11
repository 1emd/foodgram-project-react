from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models

from users.constants import MAX_LENGTH, MAX_LENGTH_EMAIL


class User(AbstractUser):
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']
    email = models.EmailField(
        max_length=MAX_LENGTH_EMAIL,
        unique=True,
        verbose_name='Email',
    )
    username = models.CharField(
        max_length=MAX_LENGTH,
        unique=True,
        validators=[UnicodeUsernameValidator(), ],
        verbose_name='Логин',
    )
    first_name = models.CharField(
        max_length=MAX_LENGTH,
        verbose_name='Имя',
    )
    last_name = models.CharField(
        max_length=MAX_LENGTH,
        verbose_name='Фамилия',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )

    class Meta:
        ordering = ('-created_at', )
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username


class Subscription(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscriptions',
        verbose_name='Подписчик',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscribed_by',
        verbose_name='Автор',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата подписки'
    )

    class Meta:
        ordering = ('-created_at', )
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'author'),
                name='unique_user_author'
            ),
            models.CheckConstraint(
                check=~models.Q(user=models.F('author')),
                name='prevent_self_subscription'
            ),
        )

    def __str__(self):
        return (f'Пользователь {self.user} '
                f'добавил автора {self.author} в Подписки.')
