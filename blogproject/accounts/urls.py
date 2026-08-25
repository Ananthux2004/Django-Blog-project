from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("register/", views.register, name="register"),
    path("login/", views.AuthLoginView.as_view(), name="login"),
    path("logout/", views.AuthLogoutView.as_view(), name="logout"),
    path(
        "password-change/",
        views.AuthPasswordChangeView.as_view(),
        name="password_change",
    ),
    path(
        "password-reset/",
        views.AuthPasswordResetView.as_view(),
        name="password_reset",
    ),
    path(
        "password-reset/done/",
        views.password_reset_done,
        name="password_reset_done",
    ),
    path(
        "password-reset-confirm/<uidb64>/<token>/",
        views.AuthPasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path(
        "password-reset/complete/",
        views.password_reset_complete,
        name="password_reset_complete",
    ),
    path('settings/', views.AccountSettingsView.as_view(), name='settings'),
]
