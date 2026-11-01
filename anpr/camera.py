"""
Webcam and Frame Capture Module for SmartPark AI
Supports both local OpenCV VideoCapture and browser-streamed frames via Base64.
Includes failure handling and mock fallback frames for robust offline testing.
"""
import os
import cv2
import numpy as np
from typing import Optional, Tuple

_CAMERA_CAPTURE: Optional[cv2.VideoCapture] = None

def get_camera(camera_index: int = 0) -> Optional[cv2.VideoCapture]:
    """Initializes or retrieves local OpenCV camera device."""
    global _CAMERA_CAPTURE
    if _CAMERA_CAPTURE is None or not _CAMERA_CAPTURE.isOpened():
        print(f"[Camera] Initializing local camera index {camera_index}...")
        # DirectShow on Windows avoids initialization hangs
        _CAMERA_CAPTURE = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
        if not _CAMERA_CAPTURE.isOpened():
            # Fallback to default backend
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

def get_fallback_demo_frame() -> np.ndarray:
    """Returns a realistic Indian vehicle frame from the dataset if physical camera is not connected."""
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

    # Synthesize fallback canvas with plate graphic
    canvas = np.full((480, 640, 3), 235, dtype=np.uint8)
    # Draw car bumper
    cv2.rectangle(canvas, (100, 150), (540, 420), (50, 50, 60), -1)
    # Draw white number plate
    cv2.rectangle(canvas, (200, 260), (440, 330), (255, 255, 255), -1)
    cv2.rectangle(canvas, (200, 260), (440, 330), (0, 0, 0), 2)
    # Blue IND strip
    cv2.rectangle(canvas, (200, 260), (230, 330), (180, 80, 20), -1)
    cv2.putText(canvas, "IND", (205, 300), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
    # Registration text
    cv2.putText(canvas, "DL01AB1234", (245, 305), cv2.FONT_HERSHEY_DUPLEX, 0.8, (0, 0, 0), 2)
    return canvas

