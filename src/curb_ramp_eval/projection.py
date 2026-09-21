from __future__ import annotations

import math


def target_crop_directional(
    image,
    signed_heading_difference_degrees: float,
    assumed_horizontal_fov_degrees: float = 90.0,
    output_size: int = 518,
    vertical_target_fraction: float = 0.64,
):
    try:
        import cv2
    except ImportError as exc:
        raise RuntimeError("OpenCV is required to construct target crops") from exc

    if abs(signed_heading_difference_degrees) > assumed_horizontal_fov_degrees / 2:
        raise ValueError("Target bearing falls outside the assumed directional field of view")
    height, width = image.shape[:2]
    target_x = width * (
        0.5 + signed_heading_difference_degrees / assumed_horizontal_fov_degrees
    )
    target_y = height * vertical_target_fraction
    crop_size = max(32, min(round(width * 0.42), round(height * 0.76)))
    left = round(target_x - crop_size / 2)
    top = round(target_y - crop_size / 2)
    left = max(0, min(left, width - crop_size))
    top = max(0, min(top, height - crop_size))
    crop = image[top : top + crop_size, left : left + crop_size]
    if crop.size == 0:
        raise ValueError("Directional target crop is empty")
    return cv2.resize(crop, (output_size, output_size), interpolation=cv2.INTER_CUBIC)


def panorama_to_perspective(
    panorama,
    center_yaw_degrees: float,
    horizontal_fov_degrees: float = 90.0,
    center_pitch_degrees: float = -10.0,
    output_width: int = 768,
    output_height: int = 512,
):
    try:
        import cv2
        import numpy as np
    except ImportError as exc:
        raise RuntimeError("OpenCV and NumPy are required for panorama projection") from exc

    pano_height, pano_width = panorama.shape[:2]
    horizontal_fov = math.radians(horizontal_fov_degrees)
    vertical_fov = 2 * math.atan(
        math.tan(horizontal_fov / 2) * output_height / output_width
    )
    x = np.linspace(-math.tan(horizontal_fov / 2), math.tan(horizontal_fov / 2), output_width)
    y = np.linspace(math.tan(vertical_fov / 2), -math.tan(vertical_fov / 2), output_height)
    grid_x, grid_y = np.meshgrid(x, y)
    grid_z = np.ones_like(grid_x)

    pitch = math.radians(center_pitch_degrees)
    rotated_y = grid_y * math.cos(pitch) - grid_z * math.sin(pitch)
    rotated_z = grid_y * math.sin(pitch) + grid_z * math.cos(pitch)
    yaw = np.arctan2(grid_x, rotated_z) + math.radians(center_yaw_degrees)
    latitude = np.arctan2(rotated_y, np.sqrt(grid_x * grid_x + rotated_z * rotated_z))

    map_x = ((yaw / (2 * math.pi) + 0.5) % 1.0 * pano_width).astype(np.float32)
    map_y = ((0.5 - latitude / math.pi) * pano_height).astype(np.float32)
    return cv2.remap(
        panorama,
        map_x,
        map_y,
        interpolation=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_WRAP,
    )

