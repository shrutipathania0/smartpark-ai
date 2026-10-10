import streamlit as st
import config
from database import db_manager
from modules import analytics_engine
from assets import ui_theme

st.set_page_config(page_title="Overview — SmartPark AI", page_icon="📊", layout="wide")

ui_theme.inject_custom_theme()

st.markdown("""
<div class="smart-banner" style="padding: 20px 28px;">
    <h1>📊 Facility Overview & Live Parking Grid</h1>
    <p>Real-time slot occupancy visualizer, zone capacity distribution, and live event monitoring.</p>
</div>
""", unsafe_allow_html=True)

# Fetch Live Slots Data
slots = db_manager.get_all_slots()
total = len(slots)
available = [s for s in slots if s["status"] == "available"]
occupied = [s for s in slots if s["status"] == "occupied"]
reserved = [s for s in slots if s["status"] == "reserved"]

# Top Metrics Row
st.markdown("### ⚡ Real-Time Facility Metrics")
m1, m2, m3, m4 = st.columns(4)

with m1:
    st.markdown(f"""
    <div class="glass-card" style="border-top:4px solid #00B4D8;">
        <div style="color:#94A3B8; font-size:0.8rem; font-weight:700; text-transform:uppercase;">Total Facility Slots</div>
        <div style="font-size:2.2rem; font-weight:800; color:#FFFFFF; margin:4px 0;">{total} Bays</div>
        <div style="color:#00B4D8; font-size:0.8rem;">4 Zones (A, B, C, D)</div>
    </div>
    """, unsafe_allow_html=True)

with m2:
    st.markdown(f"""
    <div class="glass-card" style="border-top:4px solid #00E676;">
        <div style="color:#94A3B8; font-size:0.8rem; font-weight:700; text-transform:uppercase;">Vacant & Ready</div>
        <div style="font-size:2.2rem; font-weight:800; color:#00E676; margin:4px 0;">{len(available)} Open</div>
        <div style="color:#00E676; font-size:0.8rem;">{(len(available)/total*100):.1f}% Free Capacity</div>
    </div>
    """, unsafe_allow_html=True)

with m3:
    st.markdown(f"""
    <div class="glass-card" style="border-top:4px solid #FF5252;">
        <div style="color:#94A3B8; font-size:0.8rem; font-weight:700; text-transform:uppercase;">Currently Occupied</div>
        <div style="font-size:2.2rem; font-weight:800; color:#FF5252; margin:4px 0;">{len(occupied)} Parked</div>
        <div style="color:#FF5252; font-size:0.8rem;">{(len(occupied)/total*100):.1f}% Occupancy Rate</div>
    </div>
    """, unsafe_allow_html=True)

with m4:
    st.markdown(f"""
    <div class="glass-card" style="border-top:4px solid #FFD600;">
        <div style="color:#94A3B8; font-size:0.8rem; font-weight:700; text-transform:uppercase;">Reserved Holds</div>
        <div style="font-size:2.2rem; font-weight:800; color:#FFD600; margin:4px 0;">{len(reserved)} Reserved</div>
        <div style="color:#FFD600; font-size:0.8rem;">{(len(reserved)/total*100):.1f}% Held</div>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# Legend Header
st.markdown("### 🚘 Visual Parking Lot Layout")
st.markdown("""
<div style="display:flex; gap:20px; align-items:center; margin-bottom:16px;">
    <span><span class="pulse-dot dot-green"></span><strong>Green</strong> = Vacant & Ready</span>
    <span><span class="pulse-dot dot-red"></span><strong>Red</strong> = Parked Vehicle</span>
    <span><span class="pulse-dot dot-yellow"></span><strong>Yellow</strong> = Active Reservation</span>
</div>
""", unsafe_allow_html=True)

# Zones Render
zones = ["Zone A", "Zone B", "Zone C", "Zone D"]
zone_titles = {
    "Zone A": "Zone A — Premium / Near Entrance (SUV & Standard)",
    "Zone B": "Zone B — Central Parking Lot (Standard & Compact)",
    "Zone C": "Zone C — Specialized Hub (⚡ EV Fast Charger & ♿ Accessible)",
    "Zone D": "Zone D — Economy North Lot (Budget Rates)"
}

for zone in zones:
    st.markdown(f"#### {zone_titles[zone]}")
    zone_slots = [s for s in slots if s["zone"] == zone]
    cols = st.columns(6)
    
    for i, s in enumerate(zone_slots):
        slot_id = s["slot_id"]
        status = s["status"]
        price = s["hourly_price"]
        dist = s["distance_m"]
        slot_type = s["type"]
        
        # Icon selection
        if s["has_ev"]:
            type_icon = "⚡"
        elif s["is_accessible"]:
            type_icon = "♿"
        elif slot_type == "SUV":
            type_icon = "🚙"
        else:
            type_icon = "🚗"
            
        if status == "available":
            bay_class = "bay-available"
            status_text = "🟢 VACANT"
            status_color = "#00E676"
        elif status == "occupied":
            bay_class = "bay-occupied"
            status_text = "🔴 PARKED"
            status_color = "#FF5252"
        else:
            bay_class = "bay-reserved"
            status_text = "🟡 HELD"
            status_color = "#FFD600"
            
        with cols[i % 6]:
            st.markdown(f"""
            <div class="bay-card {bay_class}">
                <div style="font-size:1.6rem; margin-bottom:2px;">{type_icon}</div>
                <div style="font-family:'Outfit', sans-serif; font-size:1.2rem; font-weight:800; color:#FFFFFF;">{slot_id}</div>
                <div style="font-size:0.75rem; font-weight:700; color:{status_color}; margin:4px 0;">{status_text}</div>
                <div style="font-size:0.75rem; color:#94A3B8;">₹{price:.0f}/hr • {dist}m</div>
            </div>
            """, unsafe_allow_html=True)
            
            # Quick Reserve button directly under bay card
            if status == "available":
                if st.button(f"Reserve {slot_id}", key=f"q_res_{slot_id}", use_container_width=True):
                    r_res = db_manager.create_reservation(slot_id=slot_id, user_name="Quick Booking", vehicle_type=slot_type, duration_mins=60)
                    if r_res["success"]:
                        st.success(f"Slot {slot_id} Reserved!")
                        st.rerun()

st.divider()

# Bottom Row: Distribution & System Event Timeline
col_left, col_right = st.columns([3, 2])

with col_left:
    st.markdown("### 📊 Status Breakdown & Utilization")
    fig_pie = analytics_engine.create_occupancy_pie_chart(slots)
    st.plotly_chart(fig_pie, use_container_width=True)

with col_right:
    st.markdown("### 📜 Real-Time System Activity Feed")
    events = db_manager.get_events(limit=8)
    if events:
        for ev in events:
            st.markdown(f"""
            <div style="background:#1E293B; border-left:3px solid #00B4D8; padding:8px 12px; border-radius:6px; margin-bottom:8px; font-size:0.85rem;">
                <span style="color:#00B4D8; font-weight:700;">[{ev['timestamp'].split(' ')[-1]}]</span>
                <strong style="color:#FFFFFF;">Slot {ev['slot_id'] or 'SYSTEM'}:</strong> {ev['details']}
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No system events recorded yet.")
