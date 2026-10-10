import streamlit as st
import os
import pathlib
import config
from database import db_manager
from assets import ui_theme

st.set_page_config(page_title="Settings & About — SmartPark AI", page_icon="⚙️", layout="wide")

ui_theme.inject_custom_theme()

st.markdown("""
<div class="smart-banner" style="padding: 20px 28px;">
    <h1>⚙️ Settings & Technical Documentation</h1>
    <p>Configure API keys, model weights, database maintenance, and view technical viva documentation.</p>
</div>
""", unsafe_allow_html=True)

tab_config, tab_viva, tab_about = st.tabs(["⚙️ Settings & Secret Config", "🎓 Technical Viva Guide", "ℹ️ About SmartPark AI"])

with tab_config:
    st.markdown("### 🔑 Groq LLM API Key Configuration")
    st.write("SmartPark AI uses an offline rule-based NLP parser by default. Optionally supply a Groq API key for enhanced natural language response generation.")
    
    current_key = config.get_groq_api_key()
    if current_key:
        st.success(f"✅ Groq API Key Detected: `{current_key[:4]}...{current_key[-4:]}`")
    else:
        st.info("ℹ️ No Groq API Key configured. Operating in Offline NLP Baseline Mode.")
        
    st.markdown("""
    #### ☁️ Streamlit Community Cloud Secret Instructions:
    To add your Groq API key in Streamlit Community Cloud:
    1. Open your app on `share.streamlit.io`
    2. Click **Settings** > **Secrets**
    3. Add the following line:
    ```toml
    GROQ_API_KEY = "your_actual_groq_api_key"
    ```
    """)
    
    st.divider()
    
    st.markdown("### 🧠 Computer Vision Model Weights")
    st.write("Manage local YOLO weights for object detection.")
    if st.button("⬇️ Download YOLOv8 Nano Model Weights (yolov8n.pt)"):
        with st.spinner("Downloading YOLOv8 weights from Ultralytics..."):
            try:
                from ultralytics import YOLO
                m = YOLO("yolov8n.pt")
                st.success("Successfully downloaded `yolov8n.pt`!")
            except Exception as e:
                st.error(f"Download failed: {e}")
                
    st.divider()
    
    st.markdown("### 🗄️ Database Maintenance")
    if st.button("⚠️ Reset & Re-Seed Database", help="Clears slots, reservations, events, and re-seeds default slot data."):
        db_path = config.DEFAULT_DB_PATH
        if os.path.exists(db_path):
            os.remove(db_path)
        db_manager.init_db()
        st.success("Database successfully reset and re-seeded!")
        st.rerun()

with tab_viva:
    st.markdown("### 🎓 Technical Viva & Architecture Guide")
    st.markdown("""
    #### 1. Computer Vision Module Architecture
    - **Dual-Engine Design:** Integrates **Ultralytics YOLOv8** object detection for precise vehicle bounding box localization (`car`, `bus`, `truck`, `motorcycle`).
    - **Fallback CV Engine:** In environments lacking PyTorch/YOLO weights, uses **OpenCV Canny Edge Density & Texture Variance** inside rectangular Slot ROIs.
    - **Overlap Metric:** Calculates **Intersection Over Slot Area (IOSA)** ratio.

    #### 2. NLP & Conversational AI Engine
    - **Intent Classification & Entity Extraction:** Built with zero-dependency regular expression syntax parsing (`nlp_processor.py`).
    - **Extracted Entities:** `vehicle_type`, `preferred_location`, `max_hourly_price`, `duration_mins`, `slot_id`, `reservation_id`, `needs_accessible`, `needs_ev`.
    - **LLM Synthesis:** Optional **Groq API** (`llama-3.3-70b-versatile`) layer polishes raw intent responses into fluid natural conversation.

    #### 3. Multi-Criteria Recommendation Algorithm
    - **Candidate Filtering:** Filters occupied/reserved slots, EV requirement mismatch, wheelchair accessibility mismatch, and maximum price limit.
    - **Multi-Factor Scoring Matrix:** Balances proximity distance, price budget, vehicle size, and preferences.

    #### 4. Database & Transactional Integrity
    - **Double-Booking Protection:** Uses SQLite `BEGIN IMMEDIATE` transaction locks before reservation creation to verify slot availability atomically.

    #### 5. Deployment Strategy
    - Prepared for **Streamlit Community Cloud** using `requirements.txt`, `packages.txt`, and relative file path resolvers.
    """)

with tab_about:
    st.markdown(f"""
    ### 🚗 {config.APP_NAME} v{config.VERSION}
    **{config.APP_TAGLINE}**
    
    Developed as an enterprise-grade Smart Mobility & Intelligent Transportation System (ITS) application.
    Combining Computer Vision, Conversational AI, Traffic Simulation, and Analytics into a single Streamlit dashboard.
    """)
