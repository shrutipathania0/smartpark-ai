# Dataset Inventory Report

**Dataset A: License Plate Detection**
- **Dataset Name:** Indian Vehicle & Truck License Plates Dataset (witvix)
- **Source URL:** https://huggingface.co/datasets/witvix/indian-truck-license-plates-sample
- **License:** CC-BY-NC-4.0 (Open Research / Academic)
- **Annotation Format:** COCO Bounding Boxes converted directly into Standard YOLO format (`0 x_center y_center width height`)
- **Total Selected Images:** 100
- **Split Distribution:**
  - Train: 70 images
  - Validation: 20 images
  - Test: 10 images
- **Classes:** 1 (`number_plate`)

**Dataset B: Plate OCR Recognition**
- **Dataset Name:** Indian License Plate Recognition Benchmark Crops
- **Format:** CSV labels + High-resolution cropped plate images
- **Total Labeled Crops:** 130
- **Label Schema:** `image_path,registration_number`
- **Verified Format:** Authentic Indian vehicle plates with state codes (RJ, DL, MH, UP, HR, etc.)
- **Split Distribution:**
  - Train: 92 plate crops
  - Val: 27 plate crops
  - Test: 11 plate crops
