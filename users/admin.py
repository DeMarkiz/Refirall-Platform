from django.contrib import admin
from users.models import UserProfile


@admin.register(UserProfile)
class UserProfile(admin.ModelAdmin):
    """
    Класс для отображения модели UserProfile в интерфейсе админки
    """

    list_display = ("user", "invite_code", "created_at")
