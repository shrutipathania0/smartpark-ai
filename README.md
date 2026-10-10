# 🚗 SmartPark AI — Intelligent Parking Management & Conversational Assistant

SmartPark AI is an enterprise-grade AI solution combining **Computer Vision**, **Natural Language Processing (NLP)**, **Traffic & Slot Simulation**, **Constraint Recommendation Algorithms**, and **Analytics** into a Streamlit dashboard.

---

## 🌟 Key Modules & Features

1. **📷 Computer Vision Occupancy Detection (`pages/2_Parking_Detection.py`)**
   - Object detection powered by Ultralytics YOLOv8 for vehicle localization (`car`, `bus`, `truck`, `motorcycle`).
   - CV Fallback engine using Canny Edge Density & Texture Variance when model weights are absent.
   - Calculates Intersection Over Slot Area (IOSA) overlap ratios to determine free/occupied status.

2. **🤖 Natural Language Parking Assistant (`pages/4_AI_Assistant.py`)**
   - Offline regex intent classifier & entity extractor (`nlp_processor.py`).
   - Extracts vehicle type, price limit, duration, location preferences, EV requirements, and slot IDs.
   - Optional Groq LLM integration (`llama-3.3-70b-versatile`) for natural language responses.

3. **🎮 Interactive Parking Simulator (`pages/3_Parking_Simulation.py`)**
   - 24-slot interactive lot across 4 zones (A, B, C, D).
   - Simulates entrance queues, random arrivals, departures, waiting times, and parking fee revenue.

4. **🎯 Multi-Criteria Recommendation Engine (`pages/5_Recommendations.py`)**
   - Multi-factor scoring matrix balancing proximity distance, price budget, vehicle size, EV charging, and accessibility.

5. **📝 Transactional Reservation System (`pages/6_Reservations.py`)**
   - SQLite persistent storage with `BEGIN IMMEDIATE` transaction locking to prevent double-booking.
   - Automatic expiration background check.

6. **📈 Business Intelligence Analytics (`pages/7_Analytics.py`)**
   - Plotly interactive charts for space distribution, zone breakdown, historical occupancy trends, and cumulative revenue.

---

## 🛠️ Technology Stack

- **Framework:** Streamlit
- **Computer Vision:** OpenCV, Ultralytics YOLOv8, Pillow
- **Data & Visuals:** Pandas, NumPy, Plotly
- **Database:** SQLite3
- **NLP / LLM:** Python Regex Engine, Groq API (`groq`)
- **Testing:** Pytest

---

## 🚀 Quickstart & Local Installation

### 1. Clone & Set Up Environment
```bash
git clone https://github.com/your-username/smartpark-ai.git
cd smartpark-ai

# Create virtual environment
python -m venv venv
# Activate on Windows:
venv\Scripts\activate
# Activate on Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Run Automated Tests
```bash
python -m pytest -q
```

### 3. Launch Streamlit Dashboard
```bash
streamlit run app.py
```

---

## ☁️ Streamlit Community Cloud Deployment

1. Push your repository to GitHub: `https://github.com/your-username/smartpark-ai`.
2. Visit [share.streamlit.io](https://share.streamlit.io/).
3. Connect your GitHub account and select repository `smartpark-ai`, branch `main`, and main file `app.py`.
4. Add optional secrets in **Settings > Secrets**:
```toml
GROQ_API_KEY = "your_actual_groq_api_key"
```
5. Click **Deploy!**

---

## 🎓 Technical Viva Q&A Guide

- **Q: How does SmartPark AI handle missing GPU hardware or model weights?**
  - *A:* The system automatically degrades gracefully to an OpenCV Canny edge-density heuristic, computing pixel texture variance within slot rectangular ROIs without throwing exceptions.
- **Q: How is double-booking prevented in the database?**
  - *A:* SQLite `BEGIN IMMEDIATE` transaction locks check the slot's current status atomically before committing any new reservation record.
- **Q: What is the recommendation scoring formula?**
  - *A:* $\\text{Score} = (0.4 \\times S_{\\text{prox}}) + (0.3 \\times S_{\\text{price}}) + (0.3 \\times S_{\\text{pref}})$.
