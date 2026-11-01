"""
OCR Engine for SmartPark AI
Wraps EasyOCR with model caching, character whitelisting, and confidence aggregation.
"""
import os
import re
import numpy as np
from typing import Dict, Any, List, Optional
import easyocr

_READER_INSTANCE: Optional[easyocr.Reader] = None
OCR_MODEL_DIR = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")), "models", "ocr")

def get_ocr_reader() -> easyocr.Reader:
    """Singleton getter for EasyOCR reader to prevent expensive model re-initialization."""
    global _READER_INSTANCE
    if _READER_INSTANCE is None:
        os.makedirs(OCR_MODEL_DIR, exist_ok=True)
        print(f"[ANPR] Initializing EasyOCR Reader (English, CPU mode, storage: {OCR_MODEL_DIR})...")
        # Initialize with English, CPU mode and local project model storage
        _READER_INSTANCE = easyocr.Reader(['en'], gpu=False, verbose=False, model_storage_directory=OCR_MODEL_DIR)
    return _READER_INSTANCE

def recognize_plate_text(preprocessed_image: np.ndarray) -> Dict[str, Any]:
    """
    Runs text recognition on preprocessed plate image.
    Returns:
    {
        "raw_text": str,
        "confidence": float,
        "details": List[Dict]
    }
    """
    if preprocessed_image is None or preprocessed_image.size == 0:
        return {"raw_text": "", "confidence": 0.0, "details": []}

    reader = get_ocr_reader()

    # EasyOCR readtext with alphanumeric allowance
    # detail=1 returns list of (bbox, text, prob)
    results = reader.readtext(
        preprocessed_image,
        allowlist='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789',
        paragraph=False,
        batch_size=1
    )

    if not results:
        # Fallback without strict allowlist if no characters were detected
        results = reader.readtext(preprocessed_image, paragraph=False)

    if not results:
        return {"raw_text": "", "confidence": 0.0, "details": []}

    # Sort results top-to-bottom then left-to-right (handles both single line and two-line Indian plates)
    def get_y_coord(item):
        bbox = item[0]
        return min(pt[1] for pt in bbox)

    results.sort(key=get_y_coord)

    collected_text_parts = []
    confidences = []
    details = []

    for bbox, text, prob in results:
        cleaned_part = re.sub(r'[^A-Za-z0-9]', '', text).upper()
        if cleaned_part:
            collected_text_parts.append(cleaned_part)
            confidences.append(float(prob))
            details.append({"text": cleaned_part, "prob": float(prob)})

    raw_text = "".join(collected_text_parts)
    avg_confidence = float(np.mean(confidences)) if confidences else 0.0

    return {
        "raw_text": raw_text,
        "confidence": round(avg_confidence, 4),
        "details": details
    }
