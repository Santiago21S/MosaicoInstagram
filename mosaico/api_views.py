"""DRF API views for the Mosaico app."""

import logging

from django.http import FileResponse
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import MosaicPackage, MosaicResult, SourceImage
from .serializers import (
    MosaicPackageCreateSerializer,
    MosaicPackageSerializer,
    MosaicResultSerializer,
    SourceImageSerializer,
    SourceImageUploadSerializer,
)
from .tasks import generate_mosaic_task

logger = logging.getLogger(__name__)

MAX_IMAGES_PER_PACKAGE = 4


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _get_user_package(request: Request, package_id: int) -> MosaicPackage:
    """Return a package owned by the requesting user or raise 404."""
    return get_object_or_404(
        MosaicPackage, pk=package_id, user=request.user
    )


# ---------------------------------------------------------------------------
# ViewSets
# ---------------------------------------------------------------------------


class MosaicPackageViewSet(viewsets.ModelViewSet):
    """CRUD operations for MosaicPackage."""

    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            MosaicPackage.objects.filter(user=self.request.user)
            .prefetch_related("images")
            .select_related("result")
        )

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return MosaicPackageCreateSerializer
        return MosaicPackageSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


# ---------------------------------------------------------------------------
# Image management
# ---------------------------------------------------------------------------


class SourceImageUploadView(APIView):
    """Upload a new source image to a package."""

    permission_classes = [IsAuthenticated]

    def post(self, request: Request, package_id: int) -> Response:
        package = _get_user_package(request, package_id)
        print('hola mundo')
        current_count = package.images.count()
        if current_count >= MAX_IMAGES_PER_PACKAGE:
            return Response(
                {"detail": f"Maximum of {MAX_IMAGES_PER_PACKAGE} images reached."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = SourceImageUploadSerializer(data=request.data)
        print(serializer.is_valid())
        print("  +++ " , serializer.errors )
        serializer.is_valid(raise_exception=True)
        print("  +++ " , serializer.errors )
        serializer.save(package=package)

        return Response(
            SourceImageSerializer(serializer.instance).data,
            status=status.HTTP_201_CREATED,
        )


class SourceImageDetailView(APIView):
    """Replace or delete a specific source image."""

    permission_classes = [IsAuthenticated]

    def _get_image(self, request: Request, package_id: int, image_id: int) -> SourceImage:
        package = _get_user_package(request, package_id)
        return get_object_or_404(SourceImage, pk=image_id, package=package)

    def put(self, request: Request, package_id: int, image_id: int) -> Response:
        image = self._get_image(request, package_id, image_id)
        serializer = SourceImageUploadSerializer(image, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(SourceImageSerializer(serializer.instance).data)

    def delete(self, request: Request, package_id: int, image_id: int) -> Response:
        image = self._get_image(request, package_id, image_id)
        image.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# Mosaic generation & delivery
# ---------------------------------------------------------------------------


class GenerateMosaicView(APIView):
    """Trigger asynchronous mosaic generation for a package."""

    permission_classes = [IsAuthenticated]

    MIN_IMAGES = 2

    def post(self, request: Request, package_id: int) -> Response:
        package = _get_user_package(request, package_id)

        # Validate image count
        image_count = package.images.count()
        if image_count < self.MIN_IMAGES:
            return Response(
                {"detail": f"At least {self.MIN_IMAGES} images are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Prevent duplicate processing
        if package.status == "processing":
            return Response(
                {"detail": "Mosaic generation is already in progress."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Dispatch Celery task
        package.status = "processing"
        package.save(update_fields=["status", "updated_at"])

        generate_mosaic_task.delay(package.id)

        return Response(
            {
                "detail": "Mosaic generation started.",
                "package_id": package.id,
                "status": package.status,
            },
            status=status.HTTP_202_ACCEPTED,
        )


class MosaicStatusView(APIView):
    """Return the current status (and result URLs if completed)."""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request, package_id: int) -> Response:
        package = _get_user_package(request, package_id)

        data: dict = {
            "package_id": package.id,
            "status": package.status,
        }

        if package.status == "completed":
            try:
                result = package.result
                data["result"] = MosaicResultSerializer(
                    result, context={"request": request}
                ).data
            except MosaicResult.DoesNotExist:
                data["result"] = None

        return Response(data)


class MosaicDownloadView(APIView):
    """Serve the generated zip file for download."""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request, package_id: int) -> Response:
        package = _get_user_package(request, package_id)

        try:
            result = package.result
        except MosaicResult.DoesNotExist:
            return Response(
                {"detail": "Mosaic has not been generated yet."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not result.zip_file:
            return Response(
                {"detail": "Zip file is not available."},
                status=status.HTTP_404_NOT_FOUND,
            )

        filename = f"mosaic_{package.id}.zip"
        return FileResponse(
            result.zip_file.open("rb"),
            as_attachment=True,
            filename=filename,
        )
