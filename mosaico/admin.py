"""Django admin configuration for the Mosaico app."""

from django.contrib import admin

from .models import MosaicPackage, MosaicResult, SourceImage


class SourceImageInline(admin.TabularInline):
    model = SourceImage
    extra = 0
    readonly_fields = ("uploaded_at",)


@admin.register(MosaicPackage)
class MosaicPackageAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "user", "status", "filter_1", "filter_2", "created_at")
    list_filter = ("status", "filter_1", "filter_2", "created_at")
    search_fields = ("title", "user__username")
    readonly_fields = ("created_at", "updated_at")
    inlines = [SourceImageInline]


@admin.register(MosaicResult)
class MosaicResultAdmin(admin.ModelAdmin):
    list_display = ("id", "package", "generated_at")
    readonly_fields = ("generated_at",)
