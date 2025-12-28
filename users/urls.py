from django.contrib.auth.views import LogoutView
from django.urls import path

from . import views

urlpatterns = [
    path("sign-up/", views.UserRegisterView.as_view(), name="sign-up"),
    path("sign-in/", views.UserLoginView.as_view(), name="sign-in"),
    path(
        "logout/",
        LogoutView.as_view(),
        name="logout",
    ),
    path("u/<str:username>/", views.UserPageView.as_view(), name="user-detail"),
]
