import re

from rest_framework import serializers
from .models import UserProfile


class LoginSerializer(serializers.Serializer):
    """
    Авторизация
    """

    phone = serializers.CharField()


class PhoneSerializer(serializers.Serializer):
    """
    Валидация номера телефона

    """

    phone = serializers.CharField(max_length=15)

    def validate_phone(self, value):
        """
        Проверка соответствия формату номера телефона

        """
        if not re.match(r"^\+7\d{10}$", value):
            raise serializers.ValidationError("Номер должен быть в формате +7XXXXXXXXXX")
        return value


class CodeSerializer(serializers.Serializer):
    """
    Валидация кода подтверждения
    """

    phone = serializers.CharField(max_length=15)
    code = serializers.CharField(max_length=4, min_length=4, help_text="4-значный код из SMS")


class UserProfileSerializer(serializers.ModelSerializer):
    activated_invite_code = serializers.SerializerMethodField()
    activated_inviter_phone = serializers.SerializerMethodField()
    invited_phones = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = ["invite_code", "activated_invite_code", "activated_inviter_phone", "invited_phones"]

    def get_activated_invite_code(self, obj):
        return obj.activated_invite.invite_code if obj.activated_invite else None

    def get_activated_inviter_phone(self, obj):
        return obj.activated_invite.user.phone if obj.activated_invite else None

    def get_invited_phones(self, obj):
        return [user.phone for user in obj.invited_users.all()]


class ActivateInviteSerializer(serializers.Serializer):
    """
    Сериализатор для активации инвайта
    """

    invite_code = serializers.CharField(max_length=6)
