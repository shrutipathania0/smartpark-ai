"""
YOLO Plate Detector for SmartPark AI
Loads custom trained or fine-tuned YOLO checkpoint, runs inference, and returns plate bounding boxes.
"""
import os
import cv2
import numpy as np
from typing import List, Dict, Any, Optional
from ultralytics import YOLO

_DETECTOR_INSTANCE: Optional[YOLO] = None
DEFAULT_MODEL_PATH = "models/detector/best.pt"
FALLBACK_MODEL_NAME = "yolov8n.pt"

def get_detector(model_path: str = DEFAULT_MODEL_PATH) -> YOLO:
    """Singleton getter for YOLO detector model."""
    global _DETECTOR_INSTANCE
    if _DETECTOR_INSTANCE is None:
        if os.path.exists(model_path):
            print(f"[ANPR] Loading custom trained detector weights from: {model_path}")
            _DETECTOR_INSTANCE = YOLO(model_path)
        else:
            print(f"[ANPR] Custom checkpoint {model_path} not found. Initializing base lightweight detector: {FALLBACK_MODEL_NAME}")
            _DETECTOR_INSTANCE = YOLO(FALLBACK_MODEL_NAME)
    return _DETECTOR_INSTANCE

def reload_detector(model_path: str = DEFAULT_MODEL_PATH):
    """Reloads detector checkpoint (used after training completes)."""
    global _DETECTOR_INSTANCE
    if os.path.exists(model_path):
        print(f"[ANPR] Reloading detector from newly trained weights: {model_path}")
        _DETECTOR_INSTANCE = YOLO(model_path)
    return _DETECTOR_INSTANCE

def detect_number_plates(
    image: np.ndarray,
    conf_threshold: float = 0.25,
    imgsz: int = 480
) -> List[Dict[str, Any]]:
    """
    Detects license plates in image frame.
    Returns list of dicts:
    [
        {
            "bbox": [x1, y1, x2, y2],
            "confidence": float,
            "class_id": int,
            "class_name": str
        }
    ]
    """
    if image is None or image.size == 0:
        return []

    model = get_detector()
    h, w = image.shape[:2]

    # Run inference with hardware-appropriate settings (imgsz=480, CPU mode)
    results = model.predict(
        source=image,
        conf=conf_threshold,
        imgsz=imgsz,
        device="cpu",
        verbose=False
    )

    detections = []
    if results and len(results) > 0:
        boxes = results[0].boxes
        for box in boxes:
            xyxy = box.xyxy[0].cpu().numpy().astype(int)
            conf = float(box.conf[0].cpu().numpy())
            cls_id = int(box.cls[0].cpu().numpy())
            cls_name = model.names.get(cls_id, "plate")

            x1, y1, x2, y2 = xyxy
            # Clamp bounds
            x1 = max(0, min(w - 1, x1))
            y1 = max(0, min(h - 1, y1))
            x2 = max(0, min(w, x2))
            y2 = max(0, min(h, y2))

            bw = x2 - x1
            bh = y2 - y1

            # Filter out microscopic or excessively large bounding boxes
            if bw > 15 and bh > 10 and bw < w * 0.98:
                detections.append({
                    "bbox": [int(x1), int(y1), int(x2), int(y2)],
                    "confidence": round(conf, 4),
                    "class_id": cls_id,
                    "class_name": cls_name
                })

    # Sort detections by confidence descending
    detections.sort(key=lambda d: d["confidence"], reverse=True)
    return detections

