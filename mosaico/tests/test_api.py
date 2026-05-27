import pytest
from rest_framework import status
from mosaico.models import MosaicPackage, SourceImage

@pytest.mark.django_db
def test_create_package_api(authenticated_client):
    """Test creating a package via POST to /api/v1/packages/."""
    url = "/api/v1/packages/"
    payload = {
        "title": "My New Package",
        "filter_1": "grayscale",
        "filter_2": "blur",
    }
    response = authenticated_client.post(url, payload)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["title"] == "My New Package"
    assert data["status"] == "pending"
    assert MosaicPackage.objects.count() == 1


@pytest.mark.django_db
def test_upload_image_api(authenticated_client, package, sample_image):
    """Test uploading an image via POST to /api/v1/packages/{id}/images/."""
    url = f"/api/v1/packages/{package.id}/images/"
    # Reset file pointer for the fixture just in case
    sample_image.seek(0)
    payload = {
        "image": sample_image,
        "order": 1,
    }
    response = authenticated_client.post(url, payload, format="multipart")
    assert response.status_code == status.HTTP_201_CREATED
    assert SourceImage.objects.filter(package=package).count() == 1


@pytest.mark.django_db
def test_max_images_validation(authenticated_client, package_with_images, sample_image):
    """Test that uploading a 5th image fails."""
    # The fixture already has 3 images. Let's upload a 4th.
    url = f"/api/v1/packages/{package_with_images.id}/images/"
    sample_image.seek(0)
    response4 = authenticated_client.post(url, {"image": sample_image, "order": 4}, format="multipart")
    assert response4.status_code == status.HTTP_201_CREATED
    assert SourceImage.objects.filter(package=package_with_images).count() == 4

    # Now upload the 5th image.
    sample_image.seek(0)
    response5 = authenticated_client.post(url, {"image": sample_image, "order": 5}, format="multipart")
    assert response5.status_code == status.HTTP_400_BAD_REQUEST
    assert "Maximum of 4 images reached." in str(response5.data) or "order" in response5.data


@pytest.mark.django_db
def test_package_access_forbidden(api_client, other_user, package):
    """Test that another user cannot access someone else's package."""
    # package belongs to 'user' fixture.
    api_client.force_authenticate(user=other_user)
    url = f"/api/v1/packages/{package.id}/"
    response = api_client.get(url)
    # The API should return 404 because get_queryset filters by request.user
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_generate_trigger_api(authenticated_client, package_with_images):
    """Test triggering the celery task via POST to generate endpoint."""
    url = f"/api/v1/packages/{package_with_images.id}/generate/"
    response = authenticated_client.post(url)
    assert response.status_code == status.HTTP_202_ACCEPTED
    package_with_images.refresh_from_db()
    # Eager mode will execute it synchronously, so status might be completed!
    assert package_with_images.status in ("processing", "completed", "failed")
@pytest.mark.django_db
def test_delete_image_api(authenticated_client, package_with_images):
    """Test deleting an image via DELETE."""
    img = package_with_images.images.first()
    url = f"/api/v1/packages/{package_with_images.id}/images/{img.id}/"
    res = authenticated_client.delete(url)
    assert res.status_code == status.HTTP_204_NO_CONTENT
    assert package_with_images.images.count() == 2

@pytest.mark.django_db
def test_get_package_status_api(authenticated_client, package):
    """Test checking package status."""
    url = f"/api/v1/packages/{package.id}/status/"
    res = authenticated_client.get(url)
    assert res.status_code == 200
    assert res.json()["status"] == "pending"
