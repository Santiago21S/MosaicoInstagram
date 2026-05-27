"""HTML URL configuration for the Mosaico app."""

from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path

from .views import PackageDetailView, PackageListView, RegisterView

urlpatterns = [
    path("", PackageListView.as_view(), name="package_list"),
    path(
        "packages/<int:pk>/",
        PackageDetailView.as_view(),
        name="package_detail",
    ),
    path(
        "login/",
        LoginView.as_view(template_name="mosaico/login.html"),
        name="login",
    ),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("register/", RegisterView.as_view(), name="register"),
]
