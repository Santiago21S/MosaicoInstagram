"""Celery tasks for asynchronous mosaic generation."""

from __future__ import annotations

import logging
import os
import uuid

from celery import shared_task
from django.conf import settings
from django.core.files import File

from .image_processing import apply_filters, create_mosaic_tiles, mix_images
from .utils import create_zip

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=0)
def generate_mosaic_task(self, package_id: int) -> None:
    """
    Generate a mosaic for the given MosaicPackage.

    Steps:
        1. Load source images and mix them into a single canvas.
        2. Apply the two selected filters sequentially.
        3. Save the mixed/filtered image.
        4. Cut the image into 3×3 tiles.
        5. Bundle tiles into a zip archive.
        6. Persist the MosaicResult.
    """
    # Import here to avoid circular imports at module load time.
    from .models import MosaicPackage, MosaicResult

    try:
        package = MosaicPackage.objects.select_related("result").get(pk=package_id)

        # 1. Collect source image paths (ordered)
        source_images = package.images.order_by("order")
        image_paths = [img.image.path for img in source_images]

        if len(image_paths) < 2:
            raise ValueError("At least 2 source images are required.")

        # 2. Mix images
        mixed = mix_images(image_paths)

        # 3. Apply filters
        filtered = apply_filters(mixed, package.filter_1, package.filter_2)

        # 4. Save mixed image to a temp location, then persist via Django storage
        unique_id = uuid.uuid4().hex[:12]
        rel_work_dir = os.path.join("tmp", f"pkg_{package_id}_{unique_id}")
        work_dir = os.path.join(settings.MEDIA_ROOT, rel_work_dir)
        os.makedirs(work_dir, exist_ok=True)

        mixed_path = os.path.join(work_dir, "mixed.jpg")
        filtered.save(mixed_path, "JPEG", quality=90)

        # 5. Create mosaic tiles
        rel_tiles_dir = os.path.join(rel_work_dir, "tiles").replace("\\", "/")
        tiles_dir = os.path.join(work_dir, "tiles")
        tile_paths = create_mosaic_tiles(filtered, tiles_dir)

        # 6. Create zip
        zip_path = os.path.join(work_dir, f"mosaic_{package_id}.zip")
        create_zip(tile_paths, zip_path)

        # 7. Create or update MosaicResult
        result, _created = MosaicResult.objects.get_or_create(package=package)

        # Save mixed image via Django FileField
        with open(mixed_path, "rb") as f:
            result.mixed_image.save(
                f"mixed_{package_id}_{unique_id}.jpg",
                File(f),
                save=False,
            )

        # Save zip via Django FileField
        with open(zip_path, "rb") as f:
            result.zip_file.save(
                f"mosaic_{package_id}_{unique_id}.zip",
                File(f),
                save=False,
            )

        result.mosaic_dir = rel_tiles_dir
        result.save()

        # 8. Mark package as completed
        package.status = "completed"
        package.save(update_fields=["status", "updated_at"])

        logger.info("Mosaic generated successfully for package %s", package_id)

    except Exception:
        logger.exception("Mosaic generation failed for package %s", package_id)
        try:
            package = MosaicPackage.objects.get(pk=package_id)
            package.status = "failed"
            package.save(update_fields=["status", "updated_at"])
        except MosaicPackage.DoesNotExist:
            pass
        raise
