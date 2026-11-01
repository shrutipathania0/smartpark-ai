# Phase 1: Hardware and Environment Report

**Project:** SmartPark AI  
**Date & Time:** 2026-11-01T23:20:00+05:30  
**Inspection Mode:** Direct Local Environment Probe  

---

## 1. Hardware Inspection

| Parameter | Observed Value | Notes |
| :--- | :--- | :--- |
| **Operating System** | Windows 11 Home / Pro (Build 26200, 64-bit AMD64) | Tested via `platform.platform()` |
| **Processor (CPU)** | Intel64 Family 6 Model 140 Stepping 2 (GenuineIntel) | 4 Logical Cores / Tiger Lake Architecture |
| **Total Physical RAM** | 7.75 GB (~8.0 GB Installed) | Verified via `GlobalMemoryStatusEx` API |
| **Available RAM** | ~0.8 GB - 1.2 GB | System running active background desktop processes |
| **Storage (Disk C:)** | Total: 475.67 GB \| Free: 311.45 GB | Ample storage (>310 GB) for datasets and checkpoints |
| **Graphics Controllers** | 1. `Intel(R) UHD Graphics`<br>2. `spacedesk Graphics Adapter` | Inspected via Windows Display Driver Registry |
| **Discrete NVIDIA GPU** | **Not detected** | `nvidia-smi` not found; registry confirms Intel UHD GPU |
| **Inference & Training Mode** | **Optimized CPU (OpenMP / AVX2)** | Hardware-aware PyTorch CPU + Ultralytics lightweight Nano model |

### Honest Technical Finding: GPU & Hardware Assessment
In accordance with Rule 1 ("Inspect the computer, available hardware, installed software... before making assumptions") and Rule 7 ("Do not fabricate training results... or completed features"):
- The local laptop contains an integrated **Intel(R) UHD Graphics** processor rather than a discrete NVIDIA GPU.
- Consequently, PyTorch CPU acceleration with multi-threaded Intel OpenMP/AVX2 runtime is utilized.
- All model selection decisions are tailored specifically to this architecture: we will use ultra-lightweight models (such as `yolov8n.pt` / `yolo11n.pt`) with reduced image sizes (`imgsz=320` or `imgsz=480`), conservative batch sizes (`batch=4` or `batch=8`), and fine-tuned pretrained weights to ensure rapid inference (<100ms) without causing Out-Of-Memory (OOM) crashes on 8 GB RAM.

---

## 2. Software & Python Environment

| Component | Target / Installed Version | Status |
| :--- | :--- | :--- |
| **Base Python** | Python 3.12.4 (64-bit MSC v.1940) | Located at `AppData\Local\Programs\Python\Python312` |
| **Virtual Environment** | `smartpark-env` | Created in root workspace directory |
| **PyTorch** | PyTorch 2.15.0+cpu (`torch`, `torchvision`) | Installed in `smartpark-env` |
| **Computer Vision** | `ultralytics`, `opencv-python`, `easyocr` | Target packages |
| **Web Backend** | `Flask`, `Flask-CORS`, `Werkzeug` | Available |
| **Scientific Stack** | `numpy`, `pandas`, `matplotlib`, `scikit-learn` | Available |

---

## 3. Network & Camera Access

- **Webcam Interface:** Windows Media Foundation / DirectShow video capture interface supported via OpenCV (`cv2.VideoCapture(0)`).
- **Web Interface:** HTML5 MediaDevices API (`navigator.mediaDevices.getUserMedia`) for seamless browser-to-backend live ANPR streaming.
- **Local Run URL:** `http://127.0.0.1:8000` (zero external internet dependency during runtime).

---

## 4. Phase 1 Checklist

- [x] Machine and OS architecture inspected.
- [x] Storage, RAM, and CPU profile analyzed.
- [x] GPU presence verified and documented.
- [x] Project workspace directory structure created.
- [x] Python virtual environment initialized.
- [x] Hardware constraints integrated into model selection strategy.

