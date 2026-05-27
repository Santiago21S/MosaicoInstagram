import os
import zipfile
import pytest
from rest_framework import status
from mosaico.models import MosaicPackage

@pytest.mark.django_db
def test_full_flow_integration(authenticated_client, sample_image):
    """End-to-end integration test."""
    # 1. Create package
    response = authenticated_client.post("/api/v1/packages/", {
        "title": "E2E Test",
        "filter_1": "grayscale",
        "filter_2": "sepia",
    })
    assert response.status_code == status.HTTP_201_CREATED
    package_id = response.json()["id"]

    # 2. Upload 3 images
    for order in range(1, 4):
        sample_image.seek(0)
        res = authenticated_client.post(
            f"/api/v1/packages/{package_id}/images/",
            {"image": sample_image, "order": order},
            format="multipart"
        )
        assert res.status_code == status.HTTP_201_CREATED

    # 3. Generate mosaic
    gen_res = authenticated_client.post(f"/api/v1/packages/{package_id}/generate/")
    assert gen_res.status_code == status.HTTP_202_ACCEPTED

    # 4. Check status and wait for completion (it's eager so it's already done)
    pkg = MosaicPackage.objects.get(id=package_id)
    assert pkg.status == "completed"

    # 5. Verify ZIP content
    assert pkg.result.zip_file
    zip_path = pkg.result.zip_file.path
    assert os.path.exists(zip_path)
    
    with zipfile.ZipFile(zip_path, 'r') as z:
        files = z.namelist()
        assert len(files) == 9
        for i in range(1, 10):
            assert f"mosaic_{i}.jpg" in files

    # 6. Download ZIP endpoint
    dl_res = authenticated_client.get(f"/api/v1/packages/{package_id}/download/")
    assert dl_res.status_code == 200
    assert dl_res["Content-Type"] == "application/zip"
