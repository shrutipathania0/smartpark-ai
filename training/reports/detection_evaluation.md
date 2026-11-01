# License Plate Detector Evaluation Report

**Evaluation Split:** Independent Test Set (10% held-out unseen samples)  
**Evaluation Date:** 2026-11-01 18:18:58 UTC  
**Model Path:** `models/detector/best.pt`  

### Measured Detection Metrics
| Metric | Value | Target Benchmark | Status |
| :--- | :--- | :--- | :--- |
| **Precision** | 0.8325 | > 0.70 | PASSED |
| **Recall** | 0.9043 | > 0.65 | PASSED |
| **mAP@50** | 0.9121 | > 0.70 | PASSED |
| **mAP@50-95** | 0.6831 | > 0.40 | PASSED |

### Qualitative Analysis
- The model accurately localizes both standard single-line and dual-line commercial Indian number plates.
- The small aspect ratio and high contrast of Indian registration plates are well handled by the anchor-free YOLOv8 architecture.
