"""
Pure image-processing functions using Pillow.

These are intentionally free of Django/ORM dependencies so they can be
tested and used independently.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

from PIL import Image, ImageFilter

if TYPE_CHECKING:
    pass

# Standard output size for all mosaic operations.
CANVAS_SIZE = (1080, 1080)
TILE_GRID = 3  # 3×3
TILE_SIZE = CANVAS_SIZE[0] // TILE_GRID  # 360


# ---------------------------------------------------------------------------
# Mixing
# ---------------------------------------------------------------------------


def _resize(img: Image.Image, size: tuple[int, int] = CANVAS_SIZE) -> Image.Image:
    """Resize an image to the given size using high-quality resampling."""
    return img.resize(size, Image.LANCZOS).convert("RGB")


def mix_images(image_paths: list[str]) -> Image.Image:
    """
    Blend / composite 2-4 images into a single 1080×1080 canvas.

    * 2 images → 50 % alpha blend.
    * 3 images → left half = img1, right half = blend(img2, img3).
    * 4 images → 2×2 grid (each quadrant 540×540).
    """
    count = len(image_paths)
    if count < 2:
        raise ValueError("At least 2 images are required for mixing.")

    images = [_resize(Image.open(p)) for p in image_paths]

    if count == 2:
        return Image.blend(images[0], images[1], alpha=0.5)

    if count == 3:
        canvas = Image.new("RGB", CANVAS_SIZE)
        half_w = CANVAS_SIZE[0] // 2
        # Left half: first image
        left = images[0].crop((0, 0, half_w, CANVAS_SIZE[1]))
        # Right half: blend of images 2 and 3
        right_blend = Image.blend(images[1], images[2], alpha=0.5)
        right = right_blend.crop((half_w, 0, CANVAS_SIZE[0], CANVAS_SIZE[1]))
        canvas.paste(left, (0, 0))
        canvas.paste(right, (half_w, 0))
        return canvas

    # 4 images → 2×2 grid
    quad_size = (CANVAS_SIZE[0] // 2, CANVAS_SIZE[1] // 2)
    canvas = Image.new("RGB", CANVAS_SIZE)
    for idx, img in enumerate(images[:4]):
        resized = img.resize(quad_size, Image.LANCZOS)
        x = (idx % 2) * quad_size[0]
        y = (idx // 2) * quad_size[1]
        canvas.paste(resized, (x, y))
    return canvas


# ---------------------------------------------------------------------------
# Filters
# ---------------------------------------------------------------------------


def _apply_sepia(img: Image.Image) -> Image.Image:
    """Convert an RGB image to sepia tone."""
    gray = img.convert("L")
    sepia = Image.merge(
        "RGB",
        (
            gray.point(lambda p: min(255, int(p * 1.2))),
            gray.point(lambda p: min(255, int(p * 1.0))),
            gray.point(lambda p: min(255, int(p * 0.8))),
        ),
    )
    return sepia


_PILLOW_FILTERS: dict[str, ImageFilter.Filter | None] = {
    "blur": ImageFilter.BLUR,
    "contour": ImageFilter.CONTOUR,
    "sharpen": ImageFilter.SHARPEN,
    "emboss": ImageFilter.EMBOSS,
    "edge_enhance": ImageFilter.EDGE_ENHANCE,
    "smooth": ImageFilter.SMOOTH,
}


def apply_filter(image: Image.Image, filter_name: str) -> Image.Image:
    """
    Apply a single named filter to the image.

    Supported filters:
        grayscale, sepia, blur, contour, sharpen, emboss, edge_enhance, smooth
    """
    name = filter_name.lower().strip()

    if name == "grayscale":
        return image.convert("L").convert("RGB")

    if name == "sepia":
        return _apply_sepia(image)

    pil_filter = _PILLOW_FILTERS.get(name)
    if pil_filter is not None:
        return image.filter(pil_filter)

    raise ValueError(f"Unknown filter: {filter_name!r}")


def apply_filters(
    image: Image.Image, filter_1: str, filter_2: str
) -> Image.Image:
    """Apply two filters sequentially."""
    image = apply_filter(image, filter_1)
    image = apply_filter(image, filter_2)
    return image


# ---------------------------------------------------------------------------
# Tile creation
# ---------------------------------------------------------------------------


def create_mosaic_tiles(image: Image.Image, output_dir: str) -> list[str]:
    """
    Cut a 1080×1080 image into a 3×3 grid of 360×360 tiles.

    Tiles are saved as ``mosaic_1.jpg`` … ``mosaic_9.jpg`` inside
    *output_dir* (created if it does not exist).

    Returns the list of absolute tile file paths.
    """
    image = _resize(image, CANVAS_SIZE)
    os.makedirs(output_dir, exist_ok=True)

    paths: list[str] = []
    tile_num = 1
    for row in range(TILE_GRID):
        for col in range(TILE_GRID):
            box = (
                col * TILE_SIZE,
                row * TILE_SIZE,
                (col + 1) * TILE_SIZE,
                (row + 1) * TILE_SIZE,
            )
            tile = image.crop(box)
            tile_path = os.path.join(output_dir, f"mosaic_{tile_num}.jpg")
            tile.save(tile_path, "JPEG", quality=90)
            paths.append(tile_path)
            tile_num += 1

    return paths
