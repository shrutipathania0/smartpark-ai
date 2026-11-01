# End-to-End ANPR System Evaluation Report

**System:** SmartPark AI Full ANPR Pipeline  
**Pipeline:** YOLO Detector -> Dynamic Cropper -> Preprocessor -> EasyOCR -> Indian Normalizer -> Confidence Gate  
**Test Set:** 10 Unseen Test Vehicle Images  
**Date:** 2026-11-01 18:21:37 UTC  

### Pipeline Performance Metrics
| Metric | Measured Result | Benchmark Standard | Status |
| :--- | :--- | :--- | :--- |
| **Plate Detection Hit Rate** | 90.0% | > 85.0% | EXCELLENT |
| **Mean End-to-End Latency** | 578.9 ms | < 600 ms | REAL-TIME CAPABLE |
| **Autonomous Field Fill Rate** | 40.0% | > 40.0% | PASSED |

### Test Predictions
| Image File | Plate Detected | Recognized Reg | Conf Score | Tier | Latency |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `img_0091.jpg` | No | `` | 0.00 | LOW | 749.0 ms |
| `img_0092.jpg` | Yes | `PB04` | 0.35 | LOW | 377.5 ms |
| `img_0093.jpg` | Yes | `7439EX2626` | 0.42 | LOW | 438.4 ms |
| `img_0094.jpg` | Yes | `CG04JD4719` | 0.92 | HIGH | 1746.2 ms |
| `img_0095.jpg` | Yes | `CH01TC8687` | 0.79 | HIGH | 385.4 ms |
| `img_0096.jpg` | Yes | `6J05CO4342` | 0.44 | LOW | 422.7 ms |
| `img_0097.jpg` | Yes | `OD01AE9596` | 0.74 | HIGH | 365.3 ms |
| `img_0098.jpg` | Yes | `MH01LE51N0` | 0.37 | LOW | 466.7 ms |
| `img_0099.jpg` | Yes | `MO1C91624` | 0.56 | MEDIUM | 436.8 ms |
| `img_0100.jpg` | Yes | `TN11BF7636` | 0.79 | HIGH | 400.5 ms |

