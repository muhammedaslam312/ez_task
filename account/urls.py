from django.urls import path

from .views import (ClientUserSignupView, OpsUserSignupView, UserLoginView,
                    email_activate)

urlpatterns = [
    path(
        "auth/ops_user/register/",
        OpsUserSignupView.as_view(),
        name="ops_user_register_view",
    ),
    path(
        "auth/client_user/register/",
        ClientUserSignupView.as_view(),
        name="client_user_register_view",
    ),
    path(
        "verify/<uidb64>/<verification_token>/",
        email_activate,
        name="email_activate",
    ),
    path(
        "auth/login/",
        UserLoginView.as_view(),
        name="user_login_view",
    ),
]
