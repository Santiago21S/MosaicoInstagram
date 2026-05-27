"""DRF serializers for the Mosaico app."""

from rest_framework import serializers

from .models import MosaicPackage, MosaicResult, SourceImage


class SourceImageSerializer(serializers.ModelSerializer):
    """Serializer for listing / retrieving source images."""

    class Meta:
        model = SourceImage
        fields = ("id", "image", "order", "uploaded_at")
        read_only_fields = ("id", "image", "uploaded_at")


class MosaicResultSerializer(serializers.ModelSerializer):
    """Read-only serializer for mosaic generation results."""

    class Meta:
        model = MosaicResult
        fields = ("id", "mixed_image", "zip_file", "generated_at")
        read_only_fields = fields


class MosaicPackageSerializer(serializers.ModelSerializer):
    """
    Full representation of a MosaicPackage including nested images and result.
    Used for list / retrieve actions.
    """

    images = SourceImageSerializer(many=True, read_only=True)
    result = MosaicResultSerializer(read_only=True)

    class Meta:
        model = MosaicPackage
        fields = (
            "id",
            "title",
            "status",
            "filter_1",
            "filter_2",
            "images",
            "result",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "status", "created_at", "updated_at")


class MosaicPackageCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating / updating a MosaicPackage."""

    class Meta:
        model = MosaicPackage
        fields = ("id", "title", "status", "filter_1", "filter_2")
        read_only_fields = ("id", "status")

    def validate(self, attrs: dict) -> dict:
        if attrs.get("filter_1") and attrs.get("filter_2"):
            if attrs["filter_1"] == attrs["filter_2"]:
                raise serializers.ValidationError(
                    {"filter_2": "filter_2 must be different from filter_1."}
                )
        return attrs


class SourceImageUploadSerializer(serializers.ModelSerializer):
    """Serializer used when uploading a new source image."""

    class Meta:
        model = SourceImage
        fields = ("image", "order")
