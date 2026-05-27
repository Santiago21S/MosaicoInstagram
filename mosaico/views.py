"""Django template-based views for the Mosaico app."""

import os

from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, ListView

from .models import MosaicPackage, MosaicResult


class PackageListView(LoginRequiredMixin, ListView):
    """List all mosaic packages belonging to the current user."""

    model = MosaicPackage
    template_name = "mosaico/package_list.html"
    context_object_name = "packages"

    def get_queryset(self):
        return (
            MosaicPackage.objects.filter(user=self.request.user)
            .prefetch_related("images")
            .select_related("result")
            .order_by("-created_at")
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["filter_choices"] = MosaicPackage.FILTER_CHOICES
        return ctx


class PackageDetailView(LoginRequiredMixin, DetailView):
    """Show details for a single mosaic package."""

    model = MosaicPackage
    template_name = "mosaico/package_detail.html"
    context_object_name = "package"

    def get_queryset(self):
        return (
            MosaicPackage.objects.filter(user=self.request.user)
            .prefetch_related("images")
            .select_related("result")
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        package = self.object
        images = list(package.images.all())
        image_count = len(images)

        ctx["images"] = images
        ctx["filter_choices"] = MosaicPackage.FILTER_CHOICES

        # Build empty slot numbers for the template
        used_orders = {img.order for img in images}
        ctx["empty_slots"] = [i for i in range(1, 5) if i not in used_orders]

        # If completed, try to gather mosaic tile file paths
        ctx["tiles"] = []
        if package.status == "completed":
            try:
                result = package.result
                if result.mosaic_dir:
                    mosaic_abs = os.path.join(settings.MEDIA_ROOT, result.mosaic_dir)
                    if os.path.isdir(mosaic_abs):
                        tile_files = sorted(
                            f
                            for f in os.listdir(mosaic_abs)
                            if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp"))
                        )
                        # Build objects with .image.url style for template compat
                        class _TileProxy:
                            """Lightweight proxy so template can use tile.image.url."""

                            def __init__(self, url):
                                self.image = type("obj", (), {"url": url})()

                        rel_dir = result.mosaic_dir
                        media_root_str = str(settings.MEDIA_ROOT)
                        if os.path.isabs(rel_dir):
                            if rel_dir.startswith(media_root_str):
                                rel_dir = os.path.relpath(rel_dir, media_root_str)
                            else:
                                rel_dir = rel_dir.split("/media/")[-1]
                        rel_dir = rel_dir.replace("\\", "/")

                        media_url = settings.MEDIA_URL
                        ctx["tiles"] = [
                            _TileProxy(f"{media_url}{rel_dir}/{name}")
                            for name in tile_files[:9]
                        ]
            except MosaicResult.DoesNotExist:
                pass

        return ctx


class RegisterView(CreateView):
    """Simple user registration using Django's built-in UserCreationForm."""

    form_class = UserCreationForm
    template_name = "mosaico/register.html"
    success_url = reverse_lazy("login")

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        return response

    def get_success_url(self):
        return reverse_lazy("package_list")
