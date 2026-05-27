import pytest
from django.urls import reverse
from django.test import Client

@pytest.fixture
def html_client(user):
    client = Client()
    client.force_login(user)
    return client

@pytest.mark.skip(reason="Incompatibilidad conocida de Django Test Client con Python 3.14 (AttributeError en copy context)")
@pytest.mark.django_db
def test_package_list_view(html_client):
    """Test the package list view requires login and renders correctly."""
    url = reverse("package_list")
    response = html_client.get(url)
    assert response.status_code == 200
    assert "mosaico/package_list.html" in (t.name for t in response.templates)


@pytest.mark.skip(reason="Incompatibilidad conocida de Django Test Client con Python 3.14 (AttributeError en copy context)")
@pytest.mark.django_db
def test_package_detail_view(html_client, package):
    """Test the package detail view requires login and renders correctly."""
    url = reverse("package_detail", args=[package.id])
    response = html_client.get(url)
    assert response.status_code == 200
    assert "mosaico/package_detail.html" in (t.name for t in response.templates)
    assert package.title in response.content.decode() or f"Paquete #{package.id}" in response.content.decode()
