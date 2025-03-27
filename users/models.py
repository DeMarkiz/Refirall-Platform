import secrets

from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models


class User(AbstractUser):
    """
    Пользователь
    """

    username = None
    phone = models.CharField(max_length=15, unique=True)

    USERNAME_FIELD = "phone"
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        ordering = ["phone"]


class UserProfile(models.Model):
    """
    Профиль

    Fields:
        user : Ссылка на другую модель User
        username : Имя пользователя
        invite_code : Время создания записи
        activated_invite : Ссылка на другую запись, если пользователь активирован приглашение
        created_at : Время создания записи
    """

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    invite_code = models.CharField(max_length=6, unique=True)
    activated_invite = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL)
    invited_users = models.ManyToManyField(User, related_name="invited_by", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    def save(self, *args, **kwargs):
        """
        Если invite_code не задан, генерируем новый код при сохранении
        """
        if not self.invite_code:
            self.invite_code = self._generate_invite_code()
        super().save(*args, **kwargs)

    @staticmethod
    def _generate_invite_code():
        """
        Генерация инвайт кода
        """
        alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        while True:
            code = "".join(secrets.choice(alphabet) for _ in range(6))
            if not UserProfile.objects.filter(invite_code=code).exists():
                return code

    class Meta:
        verbose_name = "Профиль"
        verbose_name_plural = "Профиль"
        ordering = [
            "user",
            "activated_invite",
        ]


class ConfirmationCode(models.Model):
    """
    Хранение SMS-кодов

    Fields:
        phone (str): Номер телефона в формате +7XXXXXXXXXX
        code (str): 4-значный цифровой код
        created_at (datetime): Время создания записи
    """

    phone = models.CharField(max_length=15, db_index=True)
    code = models.CharField(max_length=4)
    created_at = models.DateTimeField(auto_now_add=True)
