from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from unittest.mock import patch
from users.models import UserProfile, User


class LoginAPITestCase(APITestCase):
    """
    Тест авторизации отправки SMS.
    """

    @patch("requests.get")
    def test_login_sms(self, patch_get):

        patch_get.return_value.status_code = 200
        patch_get.return_value.json.return_value = {"success": False}

        url = reverse("users:login")

        data = {"phone": "+79998883344"}

        response = self.client.post(url, data, format="json")
        patch_get.assert_called()

        # print(response.json())

        # self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response["Content-Type"], "application/json")

        response_data = response.json()
        # self.assertIn("status", response_data)
        # self.assertEqual(response_data["status"], "Код отправлен")


class ProfileAPITestCase(APITestCase):
    """
    Тестирование функционала контроллеров Profile
    """

    def setUp(self):
        """
        Подготовка исходных данных
        """

        self.user_1 = User.objects.create(phone="+79998887777")
        self.user_1_profile = UserProfile.objects.create(user=self.user_1)
        self.user_1.save()
        self.user_1_profile.save()

        self.user_2 = User.objects.create(phone="+78889993333")
        self.user_2_profile = UserProfile.objects.create(user=self.user_2)
        self.user_2.save()
        self.user_2_profile.save()

        self.client.force_authenticate(self.user_1)

    def test_get_profile(self):
        """
        Получение профиля пользователя
        """
        url = reverse("users:profile")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "invite_code": self.user_1_profile.invite_code,
                "activated_invite_code": None,
                "activated_inviter_phone": None,
                "invited_phones": [],
                "phone": self.user_1.phone,
            },
        )

    def test_post_profile(self):
        self.client.force_authenticate(self.user_2)
        url = reverse("users:profile")
        data = {"invite_code": self.user_1_profile.invite_code}
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.user_2_profile.activated_invite, self.user_1_profile)
        self.assertEqual(self.user_1_profile.invited_users.all().first(), self.user_2)
