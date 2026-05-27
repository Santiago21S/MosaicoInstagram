"""Utility helpers for the Mosaico app."""

from __future__ import annotations

import os
import zipfile


def create_zip(tile_paths: list[str], output_path: str) -> str:
    """
    Create a zip archive containing the given tile files.

    Parameters
    ----------
    tile_paths:
        Absolute paths to the tile images to include.
    output_path:
        Absolute path where the ``.zip`` file will be written.

    Returns
    -------
    str
        The *output_path* that was written.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in tile_paths:
            zf.write(path, arcname=os.path.basename(path))

    return output_path
