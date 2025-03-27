import secrets
from urllib.parse import quote

import requests
from django.core.cache import cache
from django.db import transaction

from rest_framework_simplejwt.tokens import RefreshToken

from config import settings
from config.settings import DEBUG

from .models import ConfirmationCode, User, UserProfile
from .serializers import CodeSerializer, PhoneSerializer, ActivateInviteSerializer
from .throttles import PhoneCodeThrottle, VerifyCodeThrottle

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .serializers import UserProfileSerializer


class AuthAPIView(APIView):
    """Базовый класс для аутентификации"""

    authentication_classes = []
    permission_classes = []


class LoginAPIView(AuthAPIView):
    """
    Отправка SMS для входа
    {
        "phone": "+79123456789"
    }
    """

    throttle_classes = [PhoneCodeThrottle]  # Ограничение запросов

    def post(self, request):
        # serializer = LoginSerializer(data=request.data)
        serializer = PhoneSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone = serializer.validated_data["phone"]
        code = self._generate_code()
        ConfirmationCode.objects.filter(phone=phone).delete()
        ConfirmationCode.objects.create(phone=phone, code=code)

        # Сохраняем код в кеш на 5 минут
        cache.set(f"phone_code:{phone}", code, timeout=300)

        # Отправка SMS через API
        if self._send_sms_via_api(phone, code):
            response_data = {"status": "Код отправлен"}
            if settings.DEBUG:
                response_data["debug_code"] = code
            return Response(response_data, status=status.HTTP_200_OK)

        # Очищаем код при ошибке отправки
        cache.delete(f"phone_code:{phone}")
        ConfirmationCode.objects.filter(phone=phone).delete()
        return Response({"error": "Ошибка отправки SMS"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _generate_code(self) -> str:
        """Генерация 4-значного кода"""
        return str(secrets.randbelow(10000)).zfill(4)

    def _send_sms_via_api(self, phone: str, code: str) -> bool:
        """Сервис SMS Aero API"""
        try:
            formatted_phone = phone.lstrip("+")
            encoded_text = quote(f"Ваш код подтверждения: {code}")
            encoded_sign = quote(settings.SMSAERO_SIGN)

            # Если DEBUG = True, то сообщения работают в тестовом режиме
            if DEBUG:
                api_sms = "testsend?"
            else:
                api_sms = "send?"

            url = (
                f"https://{settings.SMSAERO_EMAIL}:{settings.SMSAERO_API_KEY}"
                f"@gate.smsaero.ru/v2/sms/{api_sms}"
                f"number={formatted_phone}&"
                f"text={encoded_text}&"
                f"sign={encoded_sign}&"
                f"channel=DIRECT"
            )

            response = requests.get(requests.utils.requote_uri(url), headers={"Accept": "application/json"}, timeout=5)

            if response.status_code == 200:
                return response.json().get("success", False)

            print(f"SMS Aero ОШИБКА: {response.status_code} - {response.text}")
            return False

        except Exception as e:
            print(f"SMS Aero ОШИБКА по исключениям: {str(e)}")
            return False


class VerifyCodeView(AuthAPIView):
    """
    Проверка кода подтверждения
    {
        "phone": "+79123456789",
        "code": "1234"
    }
    """

    throttle_classes = [VerifyCodeThrottle]

    def post(self, request):
        serializer = CodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone = serializer.validated_data["phone"]
        user_code = serializer.validated_data["code"]
        cached_code = cache.get(f"phone_code:{phone}")

        confirmation_code = ConfirmationCode.objects.filter(phone=phone).order_by("-created_at").first()

        if not confirmation_code:
            return Response({"error": "Код подтверждения не найден"}, status=status.HTTP_400_BAD_REQUEST)

        if not cached_code or user_code != cached_code or confirmation_code.code != cached_code:
            ConfirmationCode.objects.filter(phone=phone).delete()
            cache.delete(f"phone_code:{phone}")
            return Response({"error": "Неверный код или срок действия истек"}, status=status.HTTP_400_BAD_REQUEST)

        user, created = User.objects.get_or_create(phone=phone)
        user_profile, created = UserProfile.objects.get_or_create(user=user)

        # if created:
        #     user.is_active = True
        #     user.save()

        cache.delete(f"phone_code:{phone}")

        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "invite_code": user_profile.invite_code,  # Возвращаем инвайт-код
            }
        )


class ProfileAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Получение информации профиля"""
        profile = request.user.profile

        serializer = UserProfileSerializer(profile)
        return Response({**serializer.data, "phone": request.user.phone})

    def post(self, request):
        """Активация инвайт-кода"""
        serializer = ActivateInviteSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        code = serializer.validated_data["invite_code"]

        try:
            profile = request.user.profile
        except UserProfile.DoesNotExist:
            return Response({"error": "Профиль не найден"}, status=status.HTTP_404_NOT_FOUND)

        if profile.activated_invite:
            return Response({"error": "Вы уже активировали инвайт-код"}, status=status.HTTP_409_CONFLICT)

        try:
            inviter_profile = UserProfile.objects.get(invite_code=code)
        except UserProfile.DoesNotExist:
            return Response({"error": "Инвайт-код не найден"}, status=status.HTTP_404_NOT_FOUND)

        if inviter_profile.user == request.user:
            return Response({"error": "Нельзя активировать свой код"}, status=status.HTTP_403_FORBIDDEN)

        with transaction.atomic():
            profile.activated_invite = inviter_profile
            profile.save(update_fields=["activated_invite"])
            inviter_profile.invited_users.add(request.user)

        return Response({"success": "Код успешно активирован"}, status=status.HTTP_200_OK)
