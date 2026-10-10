import cv2
import numpy as np
from PIL import Image
from typing import List, Dict, Any, Tuple, Optional
import os

def load_yolo_model(model_name_or_path: str = "yolov8n.pt", auto_download: bool = False):
    """
    Attempts to load an Ultralytics YOLO model.
    Only downloads if auto_download is explicitly True or local file exists.
    """
    try:
        from ultralytics import YOLO
        if os.path.exists(model_name_or_path) or auto_download:
            model = YOLO(model_name_or_path)
            return model, f"YOLO model loaded successfully ({os.path.basename(model_name_or_path)})"
        else:
            return None, f"Model weights file '{model_name_or_path}' not found locally. Click 'Download YOLO Weights' to fetch."
    except Exception as e:
        return None, f"Could not initialize YOLO model: {str(e)}"

def detect_vehicles_with_yolo(image_np: np.ndarray, model) -> List[Dict[str, Any]]:
    """
    Runs YOLO object detection on image array and filters vehicle classes (car, motorcycle, bus, truck).
    Returns list of dicts: {"bbox": [x1, y1, x2, y2], "confidence": float, "class": str}
    """
    if model is None:
        return []
        
    vehicle_class_ids = {2: "car", 3: "motorcycle", 5: "bus", 7: "truck"}
    results = model(image_np, verbose=False)
    
    vehicles = []
    for r in results:
        boxes = r.boxes
        for box in boxes:
            cls_id = int(box.cls[0].item())
            if cls_id in vehicle_class_ids:
                xyxy = box.xyxy[0].cpu().numpy().astype(int).tolist()
                conf = float(box.conf[0].item())
                vehicles.append({
                    "bbox": xyxy,
                    "confidence": round(conf, 2),
                    "class_name": vehicle_class_ids[cls_id]
                })
    return vehicles

def calculate_overlap_ratio(slot_box: List[int], vehicle_box: List[int]) -> float:
    """Calculates Intersection Over Slot Area (IOSA) ratio."""
    sx1, sy1, sx2, sy2 = slot_box
    vx1, vy1, vx2, vy2 = vehicle_box
    
    # Calculate intersection box
    ix1 = max(sx1, vx1)
    iy1 = max(sy1, vy1)
    ix2 = min(sx2, vx2)
    iy2 = min(sy2, vy2)
    
    if ix2 <= ix1 or iy2 <= iy1:
        return 0.0
        
    intersection_area = (ix2 - ix1) * (iy2 - iy1)
    slot_area = (sx2 - sx1) * (sy2 - sy1)
    
    if slot_area <= 0:
        return 0.0
        
    return intersection_area / float(slot_area)

def analyze_slot_occupancy_cv_fallback(image_np: np.ndarray, slot_box: List[int]) -> Tuple[str, float]:
    """
    Fallback Computer Vision detector using OpenCV grayscale edge/contrast density inside slot ROI.
    Returns (status, confidence_score).
    """
    h, w = image_np.shape[:2]
    x1, y1, x2, y2 = slot_box
    
    # Clamp coordinates to image boundaries
    x1, y1 = max(0, x1), max(0, y1)
    x2, y2 = min(w, x2), min(h, y2)
    
    if (x2 - x1) <= 5 or (y2 - y1) <= 5:
        return "available", 0.5
        
    roi = image_np[y1:y2, x1:x2]
    gray = cv2.cvtColor(roi, cv2.COLOR_RGB2GRAY) if len(roi.shape) == 3 else roi
    
    # Compute Canny edge density inside ROI
    edges = cv2.Canny(gray, 50, 150)
    edge_density = np.count_nonzero(edges) / float(edges.size)
    
    # Compute standard deviation of pixel intensity (textures usually mean a vehicle present)
    std_dev = np.std(gray)
    
    # Heuristic scoring
    if edge_density > 0.12 or std_dev > 45.0:
        return "occupied", round(min(0.99, edge_density * 5), 2)
    elif edge_density > 0.06 or std_dev > 30.0:
        return "uncertain", round(edge_density * 3, 2)
    else:
        return "available", round(1.0 - edge_density, 2)

def process_parking_image(
    image_input,
    slots: List[Dict[str, Any]],
    use_yolo: bool = True,
    yolo_model=None
) -> Dict[str, Any]:
    """
    Processes an input image or video frame against slot ROIs using either YOLO or CV fallback.
    Returns annotated image (RGB np.ndarray), summary metrics, slot statuses, and detection mode.
    """
    if isinstance(image_input, Image.Image):
        image_np = np.array(image_input.convert("RGB"))
    else:
        image_np = np.array(image_input)
        
    img_height, img_width = image_np.shape[:2]
    annotated = image_np.copy()
    
    slot_results = []
    mode_label = "Model Detected (YOLOv8)"
    
    # Step 1: Detect vehicles if YOLO available and requested
    vehicles = []
    if use_yolo and yolo_model is not None:
        vehicles = detect_vehicles_with_yolo(image_np, yolo_model)
    else:
        mode_label = "CV Heuristic Fallback (Edge Density)"
        
    vacant_count = 0
    occupied_count = 0
    uncertain_count = 0
    
    for slot in slots:
        slot_id = slot["slot_id"]
        # Scale bounding box if image resolution differs from standard [800x600]
        orig_bbox = slot.get("bbox", [50, 50, 150, 120])
        sx1 = int(orig_bbox[0] * (img_width / 800.0))
        sy1 = int(orig_bbox[1] * (img_height / 600.0))
        sx2 = int(orig_bbox[2] * (img_width / 800.0))
        sy2 = int(orig_bbox[3] * (img_height / 600.0))
        scaled_box = [sx1, sy1, sx2, sy2]
        
        status = "available"
        conf = 0.95
        
        if use_yolo and yolo_model is not None:
            max_overlap = 0.0
            for v in vehicles:
                overlap = calculate_overlap_ratio(scaled_box, v["bbox"])
                if overlap > max_overlap:
                    max_overlap = overlap
            
            if max_overlap >= 0.25:
                status = "occupied"
                conf = round(max_overlap, 2)
            elif max_overlap >= 0.10:
                status = "uncertain"
                conf = round(max_overlap, 2)
            else:
                status = "available"
                conf = round(1.0 - max_overlap, 2)
        else:
            status, conf = analyze_slot_occupancy_cv_fallback(image_np, scaled_box)
            
        if status == "available":
            vacant_count += 1
            color = (0, 230, 118)  # Green (RGB)
        elif status == "occupied":
            occupied_count += 1
            color = (255, 82, 82)   # Red (RGB)
        else:
            uncertain_count += 1
            color = (255, 145, 0)  # Amber / Yellow (RGB)
            
        slot_results.append({
            "slot_id": slot_id,
            "status": status,
            "confidence": conf,
            "bbox": scaled_box,
            "zone": slot.get("zone", "Zone A")
        })
        
        # Draw bounding rectangle on image
        cv2.rectangle(annotated, (sx1, sy1), (sx2, sy2), color, 3)
        label_text = f"{slot_id} ({status[0].upper()})"
        
        # Draw background label box
        (tw, th), _ = cv2.getTextSize(label_text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)
        cv2.rectangle(annotated, (sx1, sy1 - th - 6), (sx1 + tw + 6, sy1), color, -1)
        cv2.putText(annotated, label_text, (sx1 + 3, sy1 - 4), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2, cv2.LINE_AA)
        
    # Draw detected vehicle bounding boxes if YOLO active
    if vehicles:
        for v in vehicles:
            vx1, vy1, vx2, vy2 = v["bbox"]
            cv2.rectangle(annotated, (vx1, vy1), (vx2, vy2), (0, 180, 216), 2)
            v_label = f"{v['class_name']} {v['confidence']}"
            cv2.putText(annotated, v_label, (vx1, vy1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 180, 216), 1, cv2.LINE_AA)
            
    # Draw header badge
    badge_text = f"Mode: {mode_label}"
    cv2.putText(annotated, badge_text, (15, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA)
    
    total_slots = len(slots)
    occ_pct = round((occupied_count / total_slots) * 100.0, 1) if total_slots > 0 else 0.0
    
    return {
        "annotated_image": annotated,
        "total_slots": total_slots,
        "vacant_count": vacant_count,
        "occupied_count": occupied_count,
        "uncertain_count": uncertain_count,
        "occupancy_pct": occ_pct,
        "mode_label": mode_label,
        "slot_results": slot_results,
        "detected_vehicles_count": len(vehicles)
    }
