"""
Shared pytest fixtures for the Mosaico test suite.

All fixtures are automatically discovered by pytest because the file is
named ``conftest.py`` and lives inside the ``tests`` package.
"""

from __future__ import annotations

import io

import pytest
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
from rest_framework.test import APIClient

from mosaico.models import MosaicPackage, SourceImage


# ---------------------------------------------------------------------------
# Django settings overrides for tests
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _celery_eager(settings):
    """Run Celery tasks synchronously during tests."""
    settings.CELERY_TASK_ALWAYS_EAGER = True
    settings.CELERY_TASK_EAGER_PROPAGATES = True


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------


@pytest.fixture()
def user_factory(db):
    """Factory that creates and returns Django ``User`` instances."""

    def _create_user(
        username: str = "testuser",
        password: str = "testpass123",
        **kwargs,
    ) -> User:
        return User.objects.create_user(
            username=username, password=password, **kwargs
        )

    return _create_user


@pytest.fixture()
def user(user_factory) -> User:
    """A single test user."""
    return user_factory(username="testuser")


@pytest.fixture()
def other_user(user_factory) -> User:
    """A second test user for ownership / isolation tests."""
    return user_factory(username="otheruser")


# ---------------------------------------------------------------------------
# API clients
# ---------------------------------------------------------------------------


@pytest.fixture()
def api_client() -> APIClient:
    """Unauthenticated DRF ``APIClient``."""
    return APIClient()


@pytest.fixture()
def authenticated_client(api_client: APIClient, user: User) -> APIClient:
    """DRF ``APIClient`` already authenticated as *user*."""
    api_client.force_authenticate(user=user)
    return api_client


# ---------------------------------------------------------------------------
# Images
# ---------------------------------------------------------------------------


def _make_image_file(
    name: str = "test.jpg",
    size: tuple[int, int] = (100, 100),
    color: str = "red",
) -> SimpleUploadedFile:
    """Create an in-memory JPEG ``SimpleUploadedFile``."""
    img = Image.new("RGB", size, color=color)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)
    return SimpleUploadedFile(name, buf.read(), content_type="image/jpeg")


@pytest.fixture()
def sample_image() -> SimpleUploadedFile:
    """A 100×100 red-square JPEG as a ``SimpleUploadedFile``."""
    return _make_image_file()


# ---------------------------------------------------------------------------
# Packages
# ---------------------------------------------------------------------------


@pytest.fixture()
def package(user: User, db) -> MosaicPackage:
    """A MosaicPackage with default filters and no images."""
    return MosaicPackage.objects.create(
        user=user,
        title="Test Package",
        filter_1="grayscale",
        filter_2="sepia",
    )


@pytest.fixture()
def package_with_images(package: MosaicPackage) -> MosaicPackage:
    """A MosaicPackage with 3 uploaded source images."""
    for order in range(1, 4):
        img_file = _make_image_file(
            name=f"img_{order}.jpg",
            color=["red", "green", "blue"][order - 1],
        )
        SourceImage.objects.create(
            package=package,
            image=img_file,
            order=order,
        )
    return package
