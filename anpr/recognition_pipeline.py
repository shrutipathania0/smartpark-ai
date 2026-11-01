"""
End-to-End ANPR Recognition Pipeline for SmartPark AI
Connects:
Detection (YOLO) -> Cropping -> Preprocessing -> OCR (EasyOCR) -> Validation (Indian Plate Rules) -> Confidence Scoring
"""
import os
import cv2
import base64
import numpy as np
from datetime import datetime
from typing import Dict, Any, Optional

from anpr.detector import detect_number_plates
from anpr.plate_cropper import crop_plate, validate_aspect_ratio
from anpr.image_preprocessing import preprocess_plate_image
from anpr.ocr_engine import recognize_plate_text
from anpr.plate_validator import validate_and_normalize_plate
from database.database import execute_action

CAPTURES_DIR = "data/captures"

def decode_base64_image(base64_str: str) -> Optional[np.ndarray]:
    """Decodes base64 data-URL or raw base64 string to OpenCV BGR image."""
    try:
        if "," in base64_str:
            base64_str = base64_str.split(",", 1)[1]
        img_bytes = base64.b64decode(base64_str)
        nparr = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        return img
    except Exception as e:
        print(f"[ANPR] Base64 decoding error: {e}")
        return None

def encode_image_base64(image: np.ndarray) -> str:
    """Encodes OpenCV image to base64 JPEG data-URL."""
    if image is None or image.size == 0:
        return ""
    success, buffer = cv2.imencode(".jpg", image, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
    if not success:
        return ""
    b64 = base64.b64encode(buffer).decode("utf-8")
    return f"data:image/jpeg;base64,{b64}"

def save_capture_image(image: np.ndarray, gate_type: str) -> str:
    """Saves capture frame locally under data/captures/{entry,exit}/YYYY-MM-DD/."""
    date_str = datetime.utcnow().strftime("%Y-%m-%d")
    timestamp_str = datetime.utcnow().strftime("%H%M%S_%f")
    gate_dir = os.path.join(CAPTURES_DIR, gate_type.lower(), date_str)
    os.makedirs(gate_dir, exist_ok=True)

    filename = f"cap_{timestamp_str}.jpg"
    full_path = os.path.join(gate_dir, filename)
    cv2.imwrite(full_path, image)
    # Return relative path for database portability
    return os.path.relpath(full_path, start=".")

def run_anpr_pipeline(
    image: np.ndarray,
    gate_type: str = "ENTRY",
    save_capture: bool = True
) -> Dict[str, Any]:
    """
    Executes complete ANPR recognition pipeline on an input frame.
    Returns structured results including bounding box, crop preview (base64),
    raw OCR text, normalized registration, confidence tier, and validation status.
    """
    if image is None or image.size == 0:
        return {
            "success": False,
            "error": "Empty or invalid image frame.",
            "plate_detected": False,
            "registration_number": "",
            "confidence_tier": "LOW"
        }

    h, w = image.shape[:2]

    # Step 1: Detect Number Plate with YOLO
    detections = detect_number_plates(image, conf_threshold=0.15)

    if not detections:
        # Fallback heuristic: Try a central region crop if detector doesn't trigger on close-up webcam view
        center_x1 = int(w * 0.15)
        center_y1 = int(h * 0.25)
        center_x2 = int(w * 0.85)
        center_y2 = int(h * 0.85)
        best_bbox = [center_x1, center_y1, center_x2, center_y2]
        det_conf = 0.35
        plate_detected = False
    else:
        best_det = detections[0]
        best_bbox = best_det["bbox"]
        det_conf = best_det["confidence"]
        plate_detected = True

    # Step 2: Crop Number Plate
    cropped_plate = crop_plate(image, tuple(best_bbox), padding_percent=0.06)
    if cropped_plate is None or cropped_plate.size == 0:
        cropped_plate = image

    # Step 3: OpenCV Preprocessing
    preprocessed_plate = preprocess_plate_image(cropped_plate)

    # Step 4: OCR Text Recognition
    ocr_result = recognize_plate_text(preprocessed_plate)
    raw_ocr = ocr_result["raw_text"]
    ocr_conf = ocr_result["confidence"]

    # Step 5: Indian Registration Normalization & Validation
    val_result = validate_and_normalize_plate(raw_ocr)
    normalized_reg = val_result["normalized_text"]
    is_valid_format = val_result["is_valid"]
    penalty = val_result["confidence_penalty"]

    # Step 6: Calibrated Confidence Evaluation
    # Combined score weights: 40% detector, 60% OCR, discounted by format penalty
    if plate_detected:
        combined_score = (0.40 * det_conf + 0.60 * ocr_conf) * (1.0 - penalty)
    else:
        combined_score = (0.20 + 0.80 * ocr_conf) * (1.0 - penalty)

    combined_score = max(0.0, min(1.0, combined_score))

    # Determine confidence tier
    if combined_score >= 0.70 and is_valid_format:
        confidence_tier = "HIGH"
    elif combined_score >= 0.45 or (is_valid_format and len(normalized_reg) >= 8):
        confidence_tier = "MEDIUM"
    else:
        confidence_tier = "LOW"

    # Step 7: Store capture & log
    image_rel_path = ""
    if save_capture:
        try:
            image_rel_path = save_capture_image(image, gate_type)
            execute_action(
                """INSERT INTO recognition_logs 
                   (gate_type, raw_ocr_text, normalized_registration_number, confidence, image_path, recognition_status) 
                   VALUES (?, ?, ?, ?, ?, ?);""",
                (gate_type.upper(), raw_ocr, normalized_reg, round(combined_score, 4), image_rel_path, confidence_tier)
            )
        except Exception as e:
            print(f"[ANPR] Capture logging warning: {e}")

    crop_preview_b64 = encode_image_base64(cropped_plate)

    return {
        "success": True,
        "plate_detected": plate_detected,
        "bbox": best_bbox,
        "crop_preview": crop_preview_b64,
        "raw_ocr_text": raw_ocr,
        "registration_number": normalized_reg,
        "confidence": round(combined_score, 4),
        "confidence_tier": confidence_tier,
        "is_valid_format": is_valid_format,
        "format_type": val_result["format_type"],
        "state_code": val_result["state_code"],
        "capture_path": image_rel_path,
        "timestamp": datetime.utcnow().isoformat()
    }

