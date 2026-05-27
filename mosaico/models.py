"""
Models for the Mosaico app.

Three core models:
- MosaicPackage: a user's mosaic project with filter choices and status tracking.
- SourceImage: individual source images uploaded to a package (max 4, ordered).
- MosaicResult: the generated output (mixed image, tiles directory, and zip).
"""

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class MosaicPackage(models.Model):
    """
    Represents a mosaic generation request.

    A user selects two distinct image filters and uploads up to 4 source
    images.  The backend mixes them, applies the filters, and produces a
    3×3 tile mosaic delivered as a zip file.
    """

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("processing", "Processing"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    ]

    FILTER_CHOICES = [
        ("grayscale", "Grayscale"),
        ("sepia", "Sepia"),
        ("blur", "Blur"),
        ("contour", "Contour"),
        ("sharpen", "Sharpen"),
        ("emboss", "Emboss"),
        ("edge_enhance", "Edge Enhance"),
        ("smooth", "Smooth"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="packages",
    )
    title = models.CharField(max_length=128, blank=True, default="")
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="pending"
    )
    filter_1 = models.CharField(max_length=30, choices=FILTER_CHOICES)
    filter_2 = models.CharField(max_length=30, choices=FILTER_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        label = self.title or f"Package #{self.pk}"
        return f"{label} ({self.get_status_display()})"

    def clean(self) -> None:
        super().clean()
        if self.filter_1 and self.filter_2 and self.filter_1 == self.filter_2:
            raise ValidationError(
                {"filter_2": "filter_2 must be different from filter_1."}
            )


class SourceImage(models.Model):
    """An individual source image belonging to a MosaicPackage."""

    package = models.ForeignKey(
        MosaicPackage,
        on_delete=models.CASCADE,
        related_name="images",
    )
    image = models.ImageField(upload_to="originals/%Y/%m/")
    order = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(4)],
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("package", "order")
        ordering = ["order"]

    def __str__(self) -> str:
        return f"Image #{self.order} of {self.package}"


class MosaicResult(models.Model):
    """Stores the generated mosaic output for a MosaicPackage."""

    package = models.OneToOneField(
        MosaicPackage,
        on_delete=models.CASCADE,
        related_name="result",
    )
    mixed_image = models.ImageField(
        upload_to="mixed/%Y/%m/", blank=True
    )
    mosaic_dir = models.CharField(max_length=255, blank=True)
    zip_file = models.FileField(upload_to="mosaics/%Y/%m/", blank=True)
    generated_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"Result for {self.package}"
