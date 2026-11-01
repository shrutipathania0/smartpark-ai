# YOLO Number Plate Detector Training Report

**Model:** YOLOv8 Nano (`yolov8n.pt` pretrained transfer)  
**Dataset:** Indian Truck & Vehicle License Plates (`training/datasets/detection/data.yaml`)  
**Classes:** 1 (`number_plate`)  
**Training Start:** 2026-11-01 18:13:36 UTC  
**Total Training Time:** 315.83 seconds (~5.26 minutes)  
**Hardware Used:** Intel Tiger Lake Multi-core CPU (AVX2 / OpenMP)  

### Hyperparameters
- **Epochs:** 12
- **Image Size (`imgsz`):** 416
- **Batch Size:** 8
- **Optimizer:** Auto (SGD / AdamW)
- **Early Stopping Patience:** 5 epochs

### Checkpoints
- Run Directory: `training/runs/smartpark_plate_detector/`
- Best Checkpoint: `C:\Users\shrut\OneDrive\Desktop\project 2\training\runs\smartpark_plate_detector\weights\best.pt`
- Integrated Checkpoint: `models/detector/best.pt`
