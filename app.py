import streamlit as st
import config
from database import db_manager
from assets import ui_theme

# Configure Page
st.set_page_config(
    page_title=f"{config.APP_NAME} — Smart Mobility",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inject Fresh Emerald Theme
ui_theme.inject_custom_theme()

# Initialize DB
db_manager.init_db()
db_manager.auto_expire_reservations()

# Sidebar Header
st.sidebar.markdown(f"## 🚗 {config.APP_NAME}")
st.sidebar.caption("Simple & Friendly Parking Assistant")
st.sidebar.divider()

slots_summary = db_manager.get_all_slots()
total_slots = len(slots_summary)
avail_slots = len([s for s in slots_summary if s["status"] == "available"])
occ_slots = len([s for s in slots_summary if s["status"] == "occupied"])

st.sidebar.markdown("### ⚡ Quick Status")
sb1, sb2 = st.sidebar.columns(2)
sb1.metric("🟢 Free", avail_slots)
sb2.metric("🚘 Busy", occ_slots)

st.sidebar.divider()
st.sidebar.caption(f"SmartPark AI v{config.VERSION}")

# Friendly Emerald Hero Header Banner
st.markdown("""
<div class="smart-banner">
    <h1>🚗 SmartPark AI</h1>
    <p>Find available parking, reserve spaces instantly, and chat with your AI assistant.</p>
</div>
""", unsafe_allow_html=True)

# Big Friendly Quick Action Buttons Grid (Inspired by the UI screenshot)
st.markdown("### 📱 What would you like to do?")

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.markdown("""
    <div class="glass-card" style="text-align:center; background:#FFFFFF;">
        <div style="font-size:3rem; margin-bottom:4px;">🔍</div>
        <h4 style="color:#1F2937; margin:0 0 4px 0;">Find Parking</h4>
        <p style="color:#6B7280; font-size:0.85rem; margin-bottom:10px;">Check open spots & map</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Browse Spots", key="btn_h_overview", use_container_width=True):
        st.switch_page("pages/1_Overview.py")

with c2:
    st.markdown("""
    <div class="glass-card" style="text-align:center; background:#FFFFFF;">
        <div style="font-size:3rem; margin-bottom:4px;">🤖</div>
        <h4 style="color:#1F2937; margin:0 0 4px 0;">AI Assistant</h4>
        <p style="color:#6B7280; font-size:0.85rem; margin-bottom:10px;">Chat to find or book spots</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Open AI Bot", key="btn_h_ai", use_container_width=True):
        st.switch_page("pages/4_AI_Assistant.py")

with c3:
    st.markdown("""
    <div class="glass-card" style="text-align:center; background:#FFFFFF;">
        <div style="font-size:3rem; margin-bottom:4px;">🎯</div>
        <h4 style="color:#1F2937; margin:0 0 4px 0;">Best Spot</h4>
        <p style="color:#6B7280; font-size:0.85rem; margin-bottom:10px;">Top recommendations</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Get Best Spot", key="btn_h_rec", use_container_width=True):
        st.switch_page("pages/5_Recommendations.py")

with c4:
    st.markdown("""
    <div class="glass-card" style="text-align:center; background:#FFFFFF;">
        <div style="font-size:3rem; margin-bottom:4px;">📷</div>
        <h4 style="color:#1F2937; margin:0 0 4px 0;">Camera Detector</h4>
        <p style="color:#6B7280; font-size:0.85rem; margin-bottom:10px;">AI Camera Occupancy</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Open Camera", key="btn_h_cam", use_container_width=True):
        st.switch_page("pages/2_Parking_Detection.py")

st.divider()

# Live Status Quick Snapshot
st.markdown("### 📊 Lot Occupancy Overview")
k1, k2, k3 = st.columns(3)

with k1:
    st.markdown(f"""
    <div class="glass-card" style="border-left: 6px solid #4CAF50;">
        <div style="color:#6B7280; font-weight:700; font-size:0.85rem;">AVAILABLE SPACES</div>
        <div style="font-size:2.4rem; font-weight:800; color:#4CAF50; margin:4px 0;">{avail_slots} Free</div>
        <div style="color:#6B7280; font-size:0.85rem;">Ready to Park</div>
    </div>
    """, unsafe_allow_html=True)

with k2:
    st.markdown(f"""
    <div class="glass-card" style="border-left: 6px solid #EF4444;">
        <div style="color:#6B7280; font-weight:700; font-size:0.85rem;">OCCUPIED SPACES</div>
        <div style="font-size:2.4rem; font-weight:800; color:#EF4444; margin:4px 0;">{occ_slots} Parked</div>
        <div style="color:#6B7280; font-size:0.85rem;">Vehicles Parked</div>
    </div>
    """, unsafe_allow_html=True)

with k3:
    st.markdown(f"""
    <div class="glass-card" style="border-left: 6px solid #F59E0B;">
        <div style="color:#6B7280; font-weight:700; font-size:0.85rem;">TOTAL CAPACITY</div>
        <div style="font-size:2.4rem; font-weight:800; color:#1F2937; margin:4px 0;">{total_slots} Slots</div>
        <div style="color:#6B7280; font-size:0.85rem;">Across 4 Zones</div>
    </div>
    """, unsafe_allow_html=True)
