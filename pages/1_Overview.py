import streamlit as st
import config
from database import db_manager
from modules import analytics_engine
from assets import ui_theme

st.set_page_config(page_title="Parking Grid — SmartPark AI", page_icon="🟢", layout="wide")

ui_theme.inject_custom_theme()

st.markdown("""
<div class="smart-banner" style="padding: 22px 28px;">
    <h1>🚘 Live Parking Bay Map</h1>
    <p>Check available parking slots, instant status indicators, and 1-click reservations.</p>
</div>
""", unsafe_allow_html=True)

# Fetch Slots
slots = db_manager.get_all_slots()
total = len(slots)
available = [s for s in slots if s["status"] == "available"]
occupied = [s for s in slots if s["status"] == "occupied"]
reserved = [s for s in slots if s["status"] == "reserved"]

# Simple Quick Summary Row
m1, m2, m3, m4 = st.columns(4)

with m1:
    st.markdown(f"""
    <div class="glass-card" style="border-top:4px solid #4CAF50;">
        <div style="color:#6B7280; font-size:0.8rem; font-weight:700;">TOTAL CAPACITY</div>
        <div style="font-size:2rem; font-weight:800; color:#1F2937; margin:2px 0;">{total} Slots</div>
    </div>
    """, unsafe_allow_html=True)

with m2:
    st.markdown(f"""
    <div class="glass-card" style="border-top:4px solid #4CAF50;">
        <div style="color:#6B7280; font-size:0.8rem; font-weight:700;">🟢 VACANT</div>
        <div style="font-size:2rem; font-weight:800; color:#4CAF50; margin:2px 0;">{len(available)} Open</div>
    </div>
    """, unsafe_allow_html=True)

with m3:
    st.markdown(f"""
    <div class="glass-card" style="border-top:4px solid #EF4444;">
        <div style="color:#6B7280; font-size:0.8rem; font-weight:700;">🔴 OCCUPIED</div>
        <div style="font-size:2rem; font-weight:800; color:#EF4444; margin:2px 0;">{len(occupied)} Parked</div>
    </div>
    """, unsafe_allow_html=True)

with m4:
    st.markdown(f"""
    <div class="glass-card" style="border-top:4px solid #F59E0B;">
        <div style="color:#6B7280; font-size:0.8rem; font-weight:700;">🟡 RESERVED</div>
        <div style="font-size:2rem; font-weight:800; color:#F59E0B; margin:2px 0;">{len(reserved)} Held</div>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# Lot Display by Zone
zones = ["Zone A", "Zone B", "Zone C", "Zone D"]
zone_labels = {
    "Zone A": "Zone A — Entrance & SUV Spaces",
    "Zone B": "Zone B — Central Parking Lot",
    "Zone C": "Zone C — ⚡ EV Chargers & ♿ Accessible",
    "Zone D": "Zone D — Economy Budget Parking"
}

for zone in zones:
    st.markdown(f"#### {zone_labels[zone]}")
    zone_slots = [s for s in slots if s["zone"] == zone]
    cols = st.columns(6)
    
    for i, s in enumerate(zone_slots):
        slot_id = s["slot_id"]
        status = s["status"]
        price = s["hourly_price"]
        dist = s["distance_m"]
        
        if s["has_ev"]:
            type_icon = "⚡"
        elif s["is_accessible"]:
            type_icon = "♿"
        elif s["type"] == "SUV":
            type_icon = "🚙"
        else:
            type_icon = "🚗"
            
        if status == "available":
            bay_class = "bay-available"
            status_tag = "<span style='color:#4CAF50; font-weight:800;'>🟢 Free</span>"
        elif status == "occupied":
            bay_class = "bay-occupied"
            status_tag = "<span style='color:#EF4444; font-weight:800;'>🔴 Parked</span>"
        else:
            bay_class = "bay-reserved"
            status_tag = "<span style='color:#F59E0B; font-weight:800;'>🟡 Held</span>"
            
        with cols[i % 6]:
            st.markdown(f"""
            <div class="bay-card {bay_class}">
                <div style="font-size:1.8rem; margin-bottom:2px;">{type_icon}</div>
                <div style="font-size:1.2rem; font-weight:800; color:#1F2937;">{slot_id}</div>
                <div style="font-size:0.8rem; margin:4px 0;">{status_tag}</div>
                <div style="font-size:0.75rem; color:#6B7280;">₹{price:.0f}/hr • {dist}m</div>
            </div>
            """, unsafe_allow_html=True)
            
            if status == "available":
                if st.button(f"Reserve {slot_id}", key=f"ov_res_{slot_id}", use_container_width=True):
                    r_res = db_manager.create_reservation(slot_id=slot_id, user_name="Guest", vehicle_type=s["type"], duration_mins=60)
                    if r_res["success"]:
                        st.success(f"Reserved {slot_id}!")
                        st.rerun()

st.divider()

col_l, col_r = st.columns([3, 2])
with col_l:
    st.markdown("### 📊 Status Distribution")
    fig_pie = analytics_engine.create_occupancy_pie_chart(slots)
    st.plotly_chart(fig_pie, use_container_width=True)

with col_r:
    st.markdown("### 📜 Activity Stream")
    events = db_manager.get_events(limit=6)
    if events:
        for ev in events:
            st.markdown(f"• **`[{ev['timestamp'].split(' ')[-1]}]`** Slot `{ev['slot_id'] or 'SYS'}`: {ev['details']}")
    else:
        st.info("No activity logged yet.")
