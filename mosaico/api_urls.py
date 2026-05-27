"""API URL configuration for the Mosaico app."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .api_views import (
    GenerateMosaicView,
    MosaicDownloadView,
    MosaicPackageViewSet,
    MosaicStatusView,
    SourceImageDetailView,
    SourceImageUploadView,
)

router = DefaultRouter()
router.register(r"packages", MosaicPackageViewSet, basename="package")

urlpatterns = [
    path("", include(router.urls)),
    path(
        "packages/<int:package_id>/images/",
        SourceImageUploadView.as_view(),
        name="package-image-upload",
    ),
    path(
        "packages/<int:package_id>/images/<int:image_id>/",
        SourceImageDetailView.as_view(),
        name="package-image-detail",
    ),
    path(
        "packages/<int:package_id>/generate/",
        GenerateMosaicView.as_view(),
        name="package-generate",
    ),
    path(
        "packages/<int:package_id>/status/",
        MosaicStatusView.as_view(),
        name="package-status",
    ),
    path(
        "packages/<int:package_id>/download/",
        MosaicDownloadView.as_view(),
        name="package-download",
    ),
]
