"""
Image Preprocessing Pipeline for Indian License Plate OCR
Implements adaptive contrast enhancement, bilateral denoising, thresholding, and perspective sharpening.
"""
import cv2
import numpy as np

def preprocess_plate_image(crop_bgr: np.ndarray) -> np.ndarray:
    """
    Applies calibrated computer vision preprocessing to enhance OCR character clarity:
    1. Grayscale conversion.
    2. Bilateral filter for edge-preserving denoising.
    3. CLAHE (Contrast Limited Adaptive Histogram Equalization).
    4. Morphological sharpening.
    """
    if crop_bgr is None or crop_bgr.size == 0:
        return crop_bgr

    # 1. Resize to standardized OCR height (e.g., 64px or 80px) preserving aspect ratio
    target_height = 80
    h, w = crop_bgr.shape[:2]
    if h > 0:
        target_width = int(w * (target_height / float(h)))
        target_width = max(target_width, 160)
        resized = cv2.resize(crop_bgr, (target_width, target_height), interpolation=cv2.INTER_CUBIC)
    else:
        resized = crop_bgr

    # 2. Grayscale
    if len(resized.shape) == 3:
        gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
    else:
        gray = resized

    # 3. Bilateral filter to remove noise while keeping sharp edges of text
    denoised = cv2.bilateralFilter(gray, d=7, sigmaColor=75, sigmaSpace=75)

    # 4. CLAHE for robust contrast under varied Indian sunlight and shadows
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(denoised)

    # 5. Mild unsharp masking (sharpening kernel)
    kernel = np.array([[0, -1, 0],
                       [-1, 5, -1],
                       [0, -1, 0]], dtype=np.float32)
    sharpened = cv2.filter2D(enhanced, -1, kernel)

    return sharpened

def get_binary_adaptive(gray_img: np.ndarray) -> np.ndarray:
    """Computes adaptive thresholding for highly degraded or unevenly lit plates."""
    return cv2.adaptiveThreshold(
        gray_img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
    )

