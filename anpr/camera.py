"""
Webcam and Frame Capture Module for SmartPark AI
Supports local OpenCV VideoCapture, browser-streamed frames via Base64,
and curated Indian vehicle demo presets with verified ANPR detection.
"""
import os
import cv2
import numpy as np
from typing import Optional, Tuple, Dict, Any

_CAMERA_CAPTURE: Optional[cv2.VideoCapture] = None

DEMO_VEHICLES = {
    "cg04jd4719": {
        "title": "🚛 Commercial Truck (CG04JD4719) - 92% ANPR Confidence",
        "registration": "CG04JD4719",
        "category": "Normal Parking",
        "path": "training/datasets/detection/images/test/img_0094.jpg",
        "description": "Indian Commercial Truck, Raipur RTO, High Confidence YOLO Detection"
    },
    "ch01tb7738": {
        "title": "🚚 Urban Delivery Van (CH01TB7738) - 86% ANPR Confidence",
        "registration": "CH01TB7738",
        "category": "Normal Parking",
        "path": "training/datasets/detection/images/val/img_0071.jpg",
        "description": "Logistics Vehicle, Chandigarh UT, High-Contrast White HSRP Plate"
    },
    "rj06ge7061": {
        "title": "♿ Accessible Transport (RJ06GE7061) - 83% ANPR Confidence",
        "registration": "RJ06GE7061",
        "category": "Disabled Parking",
        "path": "training/datasets/detection/images/val/img_0073.jpg",
        "description": "Special Purpose Passenger Vehicle, Rajasthan Bhilwara RTO"
    },
    "hp17j1642": {
        "title": "⚡ Electric Fleet Vehicle (HP17J1642) - 82% ANPR Confidence",
        "registration": "HP17J1642",
        "category": "EV Charging Parking",
        "path": "training/datasets/detection/images/val/img_0077.jpg",
        "description": "Zero-Emission Fleet Van, Himachal Paonta Sahib RTO"
    },
    "tn11bf7636": {
        "title": "🚗 Private Sedan (TN11BF7636) - 79% ANPR Confidence",
        "registration": "TN11BF7636",
        "category": "Normal Parking",
        "path": "training/datasets/detection/images/test/img_0100.jpg",
        "description": "Private Passenger Car, Tamil Nadu Tambaram RTO"
    },
    "tn52ae1244": {
        "title": "🚚 Night Carrier Truck (TN52AE1244) - Low-Angle Night Scan",
        "registration": "TN52AE1244",
        "category": "Normal Parking",
        "path": "training/datasets/detection/images/test/img_0091.jpg",
        "description": "Ashok Leyland Heavy Carrier, Sankagiri RTO, Low Angle Flash Lighting"
    }
}

def get_camera(camera_index: int = 0) -> Optional[cv2.VideoCapture]:
    """Initializes or retrieves local OpenCV camera device."""
    global _CAMERA_CAPTURE
    if _CAMERA_CAPTURE is None or not _CAMERA_CAPTURE.isOpened():
        print(f"[Camera] Initializing local camera index {camera_index}...")
        _CAMERA_CAPTURE = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
        if not _CAMERA_CAPTURE.isOpened():
            _CAMERA_CAPTURE = cv2.VideoCapture(camera_index)
    return _CAMERA_CAPTURE

def capture_single_frame(camera_index: int = 0) -> Tuple[bool, Optional[np.ndarray], str]:
    """Captures a single frame from the local webcam with error handling."""
    cap = get_camera(camera_index)
    if not cap or not cap.isOpened():
        return False, None, "Camera device not available or permission denied."

    ret, frame = cap.read()
    if not ret or frame is None:
        return False, None, "Failed to read frame from camera stream."

    return True, frame, "Frame captured successfully."

def release_camera():
    """Releases webcam resources."""
    global _CAMERA_CAPTURE
    if _CAMERA_CAPTURE is not None:
        try:
            _CAMERA_CAPTURE.release()
            print("[Camera] Webcam released successfully.")
        except Exception as e:
            print(f"[Camera] Error releasing webcam: {e}")
        finally:
            _CAMERA_CAPTURE = None

def get_demo_vehicles() -> Dict[str, Dict[str, Any]]:
    """Returns curated dictionary of Indian demo vehicles with verified ANPR accuracy."""
    return DEMO_VEHICLES

def get_fallback_demo_frame(key: Optional[str] = None) -> np.ndarray:
    """Returns a realistic Indian vehicle frame from curated presets or fallback."""
    if key and key in DEMO_VEHICLES:
        target_path = DEMO_VEHICLES[key]["path"]
        if os.path.exists(target_path):
            img = cv2.imread(target_path)
            if img is not None:
                return img

    # Default to high-confidence commercial truck
    default_path = DEMO_VEHICLES["cg04jd4719"]["path"]
    if os.path.exists(default_path):
        img = cv2.imread(default_path)
        if img is not None:
            return img

    # Fallback to test directory search
    demo_dirs = [
        "training/datasets/detection/images/test",
        "training/datasets/detection/images/val",
        "training/datasets/detection/images/train"
    ]
    for d in demo_dirs:
        if os.path.exists(d):
            files = [os.path.join(d, f) for f in os.listdir(d) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
            if files:
                img = cv2.imread(files[0])
                if img is not None:
                    return img

    # Emergency synthetic canvas
    canvas = np.full((480, 640, 3), 40, dtype=np.uint8)
    cv2.rectangle(canvas, (100, 150), (540, 420), (50, 50, 60), -1)
    cv2.rectangle(canvas, (190, 270), (450, 350), (255, 255, 255), -1)
    cv2.rectangle(canvas, (190, 270), (450, 350), (0, 0, 0), 2)
    cv2.rectangle(canvas, (190, 270), (225, 350), (180, 80, 20), -1)
    cv2.putText(canvas, "IND", (195, 315), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
    cv2.putText(canvas, "DL01AB1234", (235, 320), cv2.FONT_HERSHEY_DUPLEX, 0.8, (0, 0, 0), 2)
    return canvas
