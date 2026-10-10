import streamlit as st
import config
from database import db_manager
from assets import ui_theme

# Configure Streamlit Page
st.set_page_config(
    page_title=f"{config.APP_NAME} — Next-Gen Mobility",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inject Custom Google Fonts & Glassmorphic CSS Theme
ui_theme.inject_custom_theme()

# Ensure Database & Schema initialized
db_manager.init_db()
db_manager.auto_expire_reservations()

# Sidebar Brand Header
st.sidebar.markdown(f"## 🚗 {config.APP_NAME}")
st.sidebar.caption(config.APP_TAGLINE)
st.sidebar.divider()

# Live Quick Metrics in Sidebar
slots_summary = db_manager.get_all_slots()
total_slots = len(slots_summary)
avail_slots = len([s for s in slots_summary if s["status"] == "available"])
occ_slots = len([s for s in slots_summary if s["status"] == "occupied"])
res_slots = len([s for s in slots_summary if s["status"] == "reserved"])

st.sidebar.markdown("### ⚡ System Status")
sb_col1, sb_col2 = st.sidebar.columns(2)
sb_col1.metric("🟢 Free", avail_slots)
sb_col2.metric("🚘 Busy", occ_slots + res_slots)

st.sidebar.divider()

groq_key = config.get_groq_api_key()
if groq_key:
    st.sidebar.success("🟢 Groq LLM Connected", icon="🤖")
else:
    st.sidebar.info("🧠 Offline Rule-Based NLP Mode", icon="ℹ️")

st.sidebar.caption(f"SmartPark AI v{config.VERSION} | SQLite Engine")

# App Main Banner Header
st.markdown("""
<div class="smart-banner">
    <h1>🚗 SmartPark AI</h1>
    <p>Next-Generation Parking Intelligence, Vision Occupancy Detection & Conversational Assistant</p>
</div>
""", unsafe_allow_html=True)

# Main Navigation Quick Launch Deck
st.markdown("### 🌟 Feature Modules Quick Access")

c_nav1, c_nav2, c_nav3, c_nav4 = st.columns(4)

with c_nav1:
    st.markdown("""
    <div class="glass-card" style="text-align:center;">
        <div style="font-size:2.8rem; margin-bottom:8px;">📷</div>
        <h4 style="color:#00B4D8; margin:0 0 6px 0;">Vision Detector</h4>
        <p style="color:#94A3B8; font-size:0.85rem; margin-bottom:12px;">YOLOv8 Camera & Upload Occupancy Analysis</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Open Detection", key="btn_nav_det", use_container_width=True):
        st.switch_page("pages/2_Parking_Detection.py")

with c_nav2:
    st.markdown("""
    <div class="glass-card" style="text-align:center;">
        <div style="font-size:2.8rem; margin-bottom:8px;">🎮</div>
        <h4 style="color:#00E676; margin:0 0 6px 0;">Traffic Simulator</h4>
        <p style="color:#94A3B8; font-size:0.85rem; margin-bottom:12px;">Interactive Arrival Queues & Real-time Parking Flows</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Open Simulator", key="btn_nav_sim", use_container_width=True):
        st.switch_page("pages/3_Parking_Simulation.py")

with c_nav3:
    st.markdown("""
    <div class="glass-card" style="text-align:center;">
        <div style="font-size:2.8rem; margin-bottom:8px;">🤖</div>
        <h4 style="color:#FFD600; margin:0 0 6px 0;">AI Assistant</h4>
        <p style="color:#94A3B8; font-size:0.85rem; margin-bottom:12px;">Conversational Bot for Search, Help & Reservations</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Open AI Bot", key="btn_nav_ai", use_container_width=True):
        st.switch_page("pages/4_AI_Assistant.py")

with c_nav4:
    st.markdown("""
    <div class="glass-card" style="text-align:center;">
        <div style="font-size:2.8rem; margin-bottom:8px;">🎯</div>
        <h4 style="color:#48CAE4; margin:0 0 6px 0;">Recommendations</h4>
        <p style="color:#94A3B8; font-size:0.85rem; margin-bottom:12px;">Smart Proximity & Budget Slot Ranking Engine</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Open Recommendations", key="btn_nav_rec", use_container_width=True):
        st.switch_page("pages/5_Recommendations.py")

st.divider()

# Live System Dashboard Highlights
st.markdown("### 📊 Facility Snapshot")

m_col1, m_col2, m_col3, m_col4 = st.columns(4)

with m_col1:
    st.markdown(f"""
    <div class="glass-card">
        <div style="color:#94A3B8; font-size:0.85rem; font-weight:700; text-transform:uppercase;">Total Capacity</div>
        <div style="font-size:2.5rem; font-weight:800; color:#FFFFFF; margin:6px 0;">{total_slots} Bays</div>
        <div style="color:#00B4D8; font-size:0.85rem;">4 Zones (A, B, C, D)</div>
    </div>
    """, unsafe_allow_html=True)

with m_col2:
    st.markdown(f"""
    <div class="glass-card">
        <div style="color:#94A3B8; font-size:0.85rem; font-weight:700; text-transform:uppercase;">Vacant Spaces</div>
        <div style="font-size:2.5rem; font-weight:800; color:#00E676; margin:6px 0;">{avail_slots} Free</div>
        <div style="color:#00E676; font-size:0.85rem;">{(avail_slots/total_slots*100):.1f}% Available</div>
    </div>
    """, unsafe_allow_html=True)

with m_col3:
    st.markdown(f"""
    <div class="glass-card">
        <div style="color:#94A3B8; font-size:0.85rem; font-weight:700; text-transform:uppercase;">Occupied Spaces</div>
        <div style="font-size:2.5rem; font-weight:800; color:#FF5252; margin:6px 0;">{occ_slots} Parked</div>
        <div style="color:#FF5252; font-size:0.85rem;">{(occ_slots/total_slots*100):.1f}% Utilized</div>
    </div>
    """, unsafe_allow_html=True)

with m_col4:
    st.markdown(f"""
    <div class="glass-card">
        <div style="color:#94A3B8; font-size:0.85rem; font-weight:700; text-transform:uppercase;">Active Holds</div>
        <div style="font-size:2.5rem; font-weight:800; color:#FFD600; margin:6px 0;">{res_slots} Reserved</div>
        <div style="color:#FFD600; font-size:0.85rem;">SmartPark Advance Booking</div>
    </div>
    """, unsafe_allow_html=True)
