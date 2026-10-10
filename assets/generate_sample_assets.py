import cv2
import numpy as np
import os
import pathlib

def create_sample_parking_image(output_path: str):
    """Generates a synthetic top-down parking lot image with slot markings and parked vehicles."""
    width, height = 800, 600
    # Dark asphalt background
    img = np.full((height, width, 3), (40, 42, 54), dtype=np.uint8)
    
    # Draw driveways & lanes (yellow dashed lines)
    cv2.line(img, (20, 140), (780, 140), (0, 215, 255), 2)
    cv2.line(img, (20, 250), (780, 250), (0, 215, 255), 2)
    cv2.line(img, (20, 360), (780, 360), (0, 215, 255), 2)
    
    # Slot coordinates matching default slots in config.py
    # Zone A: y=50..120
    # Zone B: y=160..230
    # Zone C: y=270..340
    # Zone D: y=380..450
    
    slots = [
        ("A01", [50, 50, 150, 120], True),
        ("A02", [170, 50, 270, 120], False),
        ("A03", [290, 50, 390, 120], True),
        ("A04", [410, 50, 510, 120], False),
        ("A05", [530, 50, 630, 120], True),
        ("A06", [650, 50, 750, 120], False),

        ("B01", [50, 160, 150, 230], False),
        ("B02", [170, 160, 270, 230], True),
        ("B03", [290, 160, 390, 230], False),
        ("B04", [410, 160, 510, 230], True),
        ("B05", [530, 160, 630, 230], False),
        ("B06", [650, 160, 750, 230], True),

        ("C01", [50, 270, 150, 340], True),
        ("C02", [170, 270, 270, 340], False),
        ("C03", [290, 270, 390, 340], False),
        ("C04", [410, 270, 510, 340], False),
        ("C05", [530, 270, 630, 340], True),
        ("C06", [650, 270, 750, 340], False),

        ("D01", [50, 380, 150, 450], False),
        ("D02", [170, 380, 270, 450], True),
        ("D03", [290, 380, 390, 450], False),
        ("D04", [410, 380, 510, 450], True),
        ("D05", [530, 380, 630, 450], False),
        ("D06", [650, 380, 750, 450], False),
    ]

    for slot_id, bbox, is_parked in slots:
        x1, y1, x2, y2 = bbox
        # Draw slot white border lines
        cv2.rectangle(img, (x1, y1), (x2, y2), (220, 220, 220), 2)
        # Draw slot text label
        cv2.putText(img, slot_id, (x1 + 5, y1 + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (180, 180, 180), 1)
        
        if is_parked:
            # Draw synthetic car inside rectangle (blue/red/gray vehicle body)
            cx1, cy1 = x1 + 10, y1 + 10
            cx2, cy2 = x2 - 10, y2 - 10
            car_color = (180, 100, 40) if "A" in slot_id else (50, 120, 200)
            cv2.rectangle(img, (cx1, cy1), (cx2, cy2), car_color, -1)
            cv2.rectangle(img, (cx1, cy1), (cx2, cy2), (255, 255, 255), 1)
            # Draw windshields
            cv2.rectangle(img, (cx1 + 10, cy1 + 5), (cx2 - 10, cy1 + 20), (30, 30, 30), -1)

    # Header label
    cv2.putText(img, "SMARTPARK AI - CAMERA 01 (OVERHEAD SOUTH LOT)", (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 215, 255), 2)
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    cv2.imwrite(output_path, img)
    print(f"Sample parking image created at: {output_path}")

if __name__ == "__main__":
    out = os.path.join(pathlib.Path(__file__).parent.parent, "assets", "sample_parking.png")
    create_sample_parking_image(out)
