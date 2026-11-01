"""
Plate Cropper and Bounding Box Processor
Validates bounding box dimensions, aspect ratio, and adds adaptive margin padding.
"""
import cv2
import numpy as np
from typing import Optional, Tuple, Dict, Any

def crop_plate(
    image: np.ndarray,
    bbox: Tuple[int, int, int, int],
    padding_percent: float = 0.05
) -> Optional[np.ndarray]:
    """
    Crops number plate from image using (x1, y1, x2, y2) with configurable padding.
    """
    if image is None or image.size == 0:
        return None

    h, w = image.shape[:2]
    x1, y1, x2, y2 = bbox

    bw = x2 - x1
    bh = y2 - y1

    if bw <= 5 or bh <= 5:
        return None

    # Apply padding
    pad_x = int(bw * padding_percent)
    pad_y = int(bh * padding_percent)

    cx1 = max(0, x1 - pad_x)
    cy1 = max(0, y1 - pad_y)
    cx2 = min(w, x2 + pad_x)
    cy2 = min(h, y2 + pad_y)

    crop = image[cy1:cy2, cx1:cx2]
    return crop if crop.size > 0 else None

def validate_aspect_ratio(w: int, h: int) -> bool:
    """Standard Indian vehicle number plates typically have aspect ratios between 1.5 and 6.0."""
    if h <= 0:
        return False
    ratio = float(w) / float(h)
    return 1.2 <= ratio <= 6.5

