import streamlit as st
import os
import pathlib
import config
from database import db_manager

# Configure Streamlit Page
st.set_page_config(
    page_title=f"{config.APP_NAME} — Parking Intelligence",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling (Dark Navy Theme, Glassmorphism, Metric Cards)
CUSTOM_CSS = """
<style>
    /* Dark Navy Base Theme */
    .stApp {
        background-color: #0B132B;
        color: #F8FAFC;
        font-family: 'Inter', system-ui, -apple-system, sans-serif;
    }
    
    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #1C2541 !important;
        border-right: 1px solid #1E293B;
    }
    
    /* Header Banner */
    .main-header {
        background: linear-gradient(135deg, #1C2541 0%, #00B4D8 100%);
        padding: 24px 32px;
        border-radius: 16px;
        margin-bottom: 24px;
        box-shadow: 0 10px 25px -5px rgba(0, 180, 216, 0.25);
    }
    .main-header h1 {
        color: #FFFFFF;
        font-size: 2.2rem;
        font-weight: 700;
        margin: 0;
    }
    .main-header p {
        color: #E2E8F0;
        font-size: 1.05rem;
        margin-top: 6px;
        margin-bottom: 0;
    }
    
    /* Glassmorphism Metric Cards */
    .metric-card {
        background: #1E293B;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 20px -5px rgba(0, 0, 0, 0.4);
        border-color: #00B4D8;
    }
    .metric-val {
        font-size: 2.2rem;
        font-weight: 800;
        margin: 8px 0;
    }
    .metric-lbl {
        color: #94A3B8;
        font-size: 0.88rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        font-weight: 600;
    }
    
    /* Status Badges */
    .badge-available {
        background-color: rgba(0, 230, 118, 0.15);
        color: #00E676;
        border: 1px solid #00E676;
        padding: 4px 12px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .badge-occupied {
        background-color: rgba(255, 82, 82, 0.15);
        color: #FF5252;
        border: 1px solid #FF5252;
        padding: 4px 12px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .badge-reserved {
        background-color: rgba(255, 214, 0, 0.15);
        color: #FFD600;
        border: 1px solid #FFD600;
        padding: 4px 12px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    
    /* Custom Buttons */
    div.stButton > button:first-child {
        background: linear-gradient(135deg, #00B4D8 0%, #0077B6 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 10px 24px;
        font-weight: 600;
        transition: all 0.2s ease;
    }
    div.stButton > button:first-child:hover {
        background: linear-gradient(135deg, #48CAE4 0%, #00B4D8 100%);
        box-shadow: 0 4px 12px rgba(0, 180, 216, 0.4);
    }
    
    /* Hide default Streamlit menu & footer padding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# Ensure Database & Initial Data exist
db_manager.init_db()
db_manager.auto_expire_reservations()

# Sidebar Navigation Header
st.sidebar.markdown(f"### 🚗 {config.APP_NAME}")
st.sidebar.caption(config.APP_TAGLINE)
st.sidebar.divider()

# Sidebar System Health Status
slots_summary = db_manager.get_all_slots()
total_slots = len(slots_summary)
avail_slots = len([s for s in slots_summary if s["status"] == "available"])
occ_slots = len([s for s in slots_summary if s["status"] == "occupied"])
res_slots = len([s for s in slots_summary if s["status"] == "reserved"])

st.sidebar.markdown("#### ⚡ Live Status")
col_s1, col_s2 = st.sidebar.columns(2)
col_s1.metric("Available", avail_slots)
col_s2.metric("Occupied", occ_slots + res_slots)

st.sidebar.divider()

# Groq API Status check
groq_key = config.get_groq_api_key()
if groq_key:
    st.sidebar.success("🟢 Groq LLM Connected", icon="🤖")
else:
    st.sidebar.info("ℹ️ Offline NLP Baseline Mode (No Groq Key)", icon="🧠")

st.sidebar.caption(f"SmartPark AI v{config.VERSION} | SQLite Engine")

# Welcome Header on App Entry
st.markdown("""
<div class="main-header">
    <h1>🚗 SmartPark AI</h1>
    <p>Intelligent Parking Management, Vision Occupancy Detection & Conversational Assistant</p>
</div>
""", unsafe_allow_html=True)

# Quick Launch Cards if land on main app.py
st.markdown("### 🌟 Explore Application Modules")

m_col1, m_col2, m_col3, m_col4 = st.columns(4)

with m_col1:
    st.markdown("""
    <div class="metric-card">
        <div style="font-size: 2.5rem;">📷</div>
        <div class="metric-val" style="color:#00B4D8;">Vision</div>
        <div class="metric-lbl">Camera & Image Detection</div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Open Detection", key="nav_det"):
        st.switch_page("pages/2_Parking_Detection.py")

with m_col2:
    st.markdown("""
    <div class="metric-card">
        <div style="font-size: 2.5rem;">🎮</div>
        <div class="metric-val" style="color:#00E676;">Simulator</div>
        <div class="metric-lbl">Traffic & Slot Controls</div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Open Simulator", key="nav_sim"):
        st.switch_page("pages/3_Parking_Simulation.py")

with m_col3:
    st.markdown("""
    <div class="metric-card">
        <div style="font-size: 2.5rem;">🤖</div>
        <div class="metric-val" style="color:#FFD600;">AI Assistant</div>
        <div class="metric-lbl">Conversational Bot</div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Open Assistant", key="nav_ai"):
        st.switch_page("pages/4_AI_Assistant.py")

with m_col4:
    st.markdown("""
    <div class="metric-card">
        <div style="font-size: 2.5rem;">📊</div>
        <div class="metric-val" style="color:#FF5252;">Analytics</div>
        <div class="metric-lbl">Charts & Revenue Logs</div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Open Analytics", key="nav_ana"):
        st.switch_page("pages/7_Analytics.py")

st.divider()

# Quick Overview Dashboard Metrics
st.markdown("### 📊 System Quick Snapshot")
c1, c2, c3, c4 = st.columns(4)

with c1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-lbl">Total Capacity</div>
        <div class="metric-val" style="color:#F8FAFC;">{total_slots}</div>
        <div style="color:#94A3B8; font-size:0.8rem;">4 Zones (A, B, C, D)</div>
    </div>
    """, unsafe_allow_html=True)

with c2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-lbl">Vacant Spaces</div>
        <div class="metric-val" style="color:#00E676;">{avail_slots}</div>
        <div style="color:#00E676; font-size:0.8rem;">{(avail_slots/total_slots*100):.1f}% Available</div>
    </div>
    """, unsafe_allow_html=True)

with c3:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-lbl">Occupied Spaces</div>
        <div class="metric-val" style="color:#FF5252;">{occ_slots}</div>
        <div style="color:#FF5252; font-size:0.8rem;">{(occ_slots/total_slots*100):.1f}% Parked</div>
    </div>
    """, unsafe_allow_html=True)

with c4:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-lbl">Active Reservations</div>
        <div class="metric-val" style="color:#FFD600;">{res_slots}</div>
        <div style="color:#FFD600; font-size:0.8rem;">Held via SmartPark</div>
    </div>
    """, unsafe_allow_html=True)
