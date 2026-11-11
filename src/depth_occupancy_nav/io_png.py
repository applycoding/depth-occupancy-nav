# SPDX-License-Identifier: Apache-2.0
"""16-bit depth PNG encode and decode via Pillow."""

from __future__ import annotations

import io

import numpy as np
from PIL import Image

from depth_occupancy_nav.camera import Camera


def encode_depth_png_mm(depth: np.ndarray) -> bytes:
    """Encode depth as 16-bit unsigned PNG in millimetres; invalid = 0."""
    mm = np.zeros(depth.shape, dtype=np.uint16)
    valid = depth > 0
    mm[valid] = np.round(depth[valid] * 1000.0).astype(np.uint16)
    h, w = mm.shape
    img = Image.new("I;16", (w, h))
    img.putdata(mm.flatten().tolist())
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def decode_depth_png_mm(data: bytes, camera: Camera | None = None) -> np.ndarray:
    cam = camera or Camera()
    img = Image.open(io.BytesIO(data))
    arr = np.array(img, dtype=np.uint16)
    if arr.shape != (cam.height, cam.width):
        arr = arr.reshape((cam.height, cam.width))
    depth = np.zeros((cam.height, cam.width), dtype=np.float64)
    valid = arr > 0
    depth[valid] = arr[valid].astype(np.float64) / 1000.0
    return depth
