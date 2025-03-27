from django.urls import path
from django.contrib.auth.views import LoginView
from users.api import LoginAPIView, VerifyCodeView, ProfileAPIView

app_name = "UsersConfig"

urlpatterns = [
    path("api/auth/login/", LoginAPIView.as_view(), name="login"),
    path("api/auth/verify-code/", VerifyCodeView.as_view(), name="verify-code"),
    path("api/profile/", ProfileAPIView.as_view(), name="profile"),
    path("", LoginView.as_view(template_name="base.html"), name="auth"),
]
