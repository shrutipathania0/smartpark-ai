import pytest
import numpy as np
from PIL import Image
from modules import vision_detector

def test_vision_fallback_detector():
    # Create synthetic test image (800x600 dark canvas)
    img_np = np.full((600, 800, 3), 40, dtype=np.uint8)
    sample_slots = [
        {"slot_id": "A01", "zone": "Zone A", "bbox": [50, 50, 150, 120]},
        {"slot_id": "A02", "zone": "Zone A", "bbox": [170, 50, 270, 120]},
    ]
    
    res = vision_detector.process_parking_image(
        image_input=img_np,
        slots=sample_slots,
        use_yolo=False,
        yolo_model=None
    )
    
    assert res["total_slots"] == 2
    assert "annotated_image" in res
    assert res["mode_label"] == "CV Heuristic Fallback (Edge Density)"

def test_vision_overlap_ratio():
    slot_box = [50, 50, 150, 120]
    vehicle_box = [50, 50, 150, 120]
    overlap = vision_detector.calculate_overlap_ratio(slot_box, vehicle_box)
    assert overlap == 1.0

    no_overlap_veh = [300, 300, 400, 400]
    overlap_zero = vision_detector.calculate_overlap_ratio(slot_box, no_overlap_veh)
    assert overlap_zero == 0.0
