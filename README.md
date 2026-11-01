# SmartPark AI — Autonomous IoT Parking & ANPR Management System

An end-to-end, locally operational, AI-powered smart parking management simulator and IoT facility controller. SmartPark AI demonstrates how modern parking facilities leverage local computer vision (YOLO Number Plate Detection + EasyOCR + Indian Registration Validation), atomic spatial slot allocation, dynamic tariff calculation, and real-time incident simulation.

---

## 1. Key Features & Interfaces

The system serves **four synchronized interfaces** from a single shared SQLite backend:

1. **Driver Entry Machine (`/entry`):**
   - Live browser webcam feed with real-time plate bounding box overlays.
   - Dual-engine ANPR pipeline (YOLO detector + CLAHE preprocessing + EasyOCR + Indian RTO normalization).
   - Calibrated confidence scoring (`HIGH`, `MEDIUM`, `LOW`) with auto-population of registration numbers.
   - Strict category selection (**Disabled Parking**, **EV Charging Parking**, **Normal Parking**).
   - Atomic slot allocation with immediate digital ticket issuance.

2. **Parking Area Monitoring (`/parking`):**
   - Interactive visual spatial grid divided by category (3 Disabled, 3 EV, 9 Normal slots).
   - Strict standardized status colors:
     - 🟢 **Green — VACANT**
     - 🟡 **Yellow — RESERVED**
     - 🔴 **Red — OCCUPIED**
     - ⚪ **Slate Grey — BLOCKED**
   - Detailed hover and click modals for every parking slot.
   - **Interactive IoT Simulation Engine:**
     - *Park Correctly:* Confirms vehicle arrival and transitions slot to OCCUPIED.
     - *Place Object:* Marks stall as BLOCKED and creates an obstruction alert.
     - *Clear Object:* Safely clears obstruction and restores valid previous slot state.
     - *Park Incorrectly:* Generates parking violation alert.
     - *Block Lane:* Simulates entry/exit lane obstruction.
     - *Cross Parking & Straddling 2 Spaces:* Logs multi-stall violations.
     - *Reset Simulation:* Clean baseline restoration.

3. **Guard Security Dashboard (`/guard`):**
   - Session-based authentication with bcrypt/pbkdf2 password hashing (`guard_admin`).
   - Live KPI cards: Total stalls, vacant, reserved, occupied, blocked, revenue, active sessions.
   - Security incident management: Real-time alert list with *Acknowledge* and *Resolve* actions.
   - **Dynamic Parking Tariff Control:** Configurable free periods, grace periods, hourly rates, and billing intervals.
   - **Pricing Snapshot Integrity:** Existing sessions lock pricing rules at parking start; tariff modifications apply exclusively to future sessions.
   - Full audit trail of historical parking sessions and camera recognition logs.

4. **Driver Exit Machine (`/exit`):**
   - Outbound camera scanning recognizing departing vehicle plates.
   - Active session matching and actual duration calculation (`exit_time - parked_start_time`).
   - Automated tariff calculation with itemized billing breakdowns.
   - Confirmation releases assigned slot to VACANT and marks session COMPLETED.
   - Unparked reservations (ticket created but vehicle never parked) cost ₹0.00.

---

## 2. Hardware Inspection & Honest Engineering Finding

In accordance with strict verification rules:
- **CPU:** Intel64 Tiger Lake Core i3-1115G4 (4 Logical Processors, AVX2 / OpenMP).
- **Physical RAM:** 7.75 GB (~0.8 GB - 1.2 GB available).
- **GPU Finding:** Windows display adapter registry inspection confirmed **Intel(R) UHD Graphics** with no discrete NVIDIA GPU installed (`nvidia-smi` absent).
- **Architecture Strategy:** The machine learning stack is optimized for high-throughput CPU inference using PyTorch CPU multi-threading and an anchor-free lightweight YOLOv8 Nano model (`imgsz=416`), completely avoiding out-of-memory crashes while achieving ~145 ms detector inference.

See [training/reports/hardware_and_environment.md](training/reports/hardware_and_environment.md) for full hardware telemetry.

---

## 3. Machine Learning & ANPR Pipeline

### 3.1 Datasets
- **Source:** Indian Truck & Vehicle License Plates Dataset (witvix / Hugging Face, CC-BY-NC-4.0).
- **Dataset A (Detection):** 100 verified Indian vehicle images converted to standard YOLO format (`0 x_center y_center width height`). Split: 70 train, 20 val, 10 test.
- **Dataset B (OCR Recognition):** 130 cropped number-plate images with verified ground-truth registration text strings and CSV schemas.
- Inventory Report: [training/reports/dataset_inventory.md](training/reports/dataset_inventory.md).
- Quality Report: [training/reports/dataset_quality_report.md](training/reports/dataset_quality_report.md).

### 3.2 Custom Trained YOLO Detector
- **Model Checkpoint:** `models/detector/best.pt`
- **Training Duration:** 315.83 seconds (5.26 mins) on CPU.
- **Evaluation on Independent Test Set:**
  - **Precision:** 83.25%
  - **Recall:** 90.43%
  - **mAP@50:** 91.21%
  - **mAP@50-95:** 68.31%
- Full Training Report: [training/reports/detection_training_report.md](training/reports/detection_training_report.md).
- Test Evaluation Report: [training/reports/detection_evaluation.md](training/reports/detection_evaluation.md).

### 3.3 OCR & Indian Plate Normalization
- Preprocessing: Resize standard height + Bilateral Filter (edge-preserving denoising) + CLAHE (contrast equalization) + Morphological Sharpening.
- OCR Engine: EasyOCR cached singleton (`models/ocr/`).
- Indian RTO Validator: Positional disambiguation (`0` vs `O`, `1` vs `I`, `8` vs `B`, `5` vs `S`, `2` vs `Z`), standard state code verification, and Bharat Series (`22BH...`) support.
- Performance: **Character Error Rate (CER) = 20.18%**, **End-to-End Plate Detection Rate = 90.0%**, **Mean E2E Latency = 578.9 ms**.
- Evaluation Reports: [training/reports/ocr_evaluation.md](training/reports/ocr_evaluation.md) & [training/reports/anpr_end_to_end_evaluation.md](training/reports/anpr_end_to_end_evaluation.md).

---

## 4. Default Parking Pricing Policy

- **Complimentary Period:** First 60 minutes free.
- **Grace Period:** Additional 10 minutes free (Total 70 minutes free).
- **Chargeable Rate:** After 70 minutes, ₹50.00 per started 2-hour billing block (`CEIL_INTERVAL`).
- **Examples:**
  - 30 mins: ₹0.00
  - 60 mins: ₹0.00
  - 70 mins: ₹0.00
  - 71 mins: ₹50.00
  - 2 hours 10 mins (130m): ₹50.00
  - 3 hours 11 mins (191m): ₹100.00

---

## 5. Deployment Options

### Option A: Local Streamlit Dashboard (One-Click)
Double-click `run_streamlit.bat` or run:
```cmd
smartpark-env\Scripts\streamlit.exe run streamlit_app.py
```
*Access locally at:* **`http://localhost:8501`**

### Option B: Local Flask Web Application (One-Click)
Double-click `run.bat` or run:
```cmd
run.bat
```
*Access locally at:* **`http://127.0.0.1:8000`**

### Option C: GitHub & Streamlit Community Cloud Deployment
1. **Push to your GitHub:**
   - Create a new repository on [GitHub](https://github.com/new) named `SmartPark-AI`.
   - Link and push this repository:
     ```bash
     git remote add origin https://github.com/<YOUR_USERNAME>/SmartPark-AI.git
     git push -u origin main
     ```
2. **Deploy to Streamlit Cloud:**
   - Go to [share.streamlit.io](https://share.streamlit.io/) and log in with your GitHub account.
   - Click **New app**.
   - Select Repository: `<YOUR_USERNAME>/SmartPark-AI`.
   - Branch: `main`.
   - Main file path: `streamlit_app.py`.
   - Click **Deploy!** Your app will be live with a public URL.

---

## 6. Automated Test Suite

Run all 32 unit and integration tests across database, allocation, pricing, simulation, and ANPR:
```cmd
smartpark-env\Scripts\python.exe -m unittest discover -s tests -p "test_*.py"
```
*Result: 32 tests executed with 100% pass rate.*

