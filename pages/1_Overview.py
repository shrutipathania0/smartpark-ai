import streamlit as st
import config
from database import db_manager
from modules import analytics_engine

st.set_page_config(page_title="Overview — SmartPark AI", page_icon="📊", layout="wide")

st.markdown("## 📊 Overview Dashboard")
st.caption("Live status of all parking zones, real-time occupancy metrics, and operational overview.")

# Fetch live slots
slots = db_manager.get_all_slots()
total = len(slots)
available = [s for s in slots if s["status"] == "available"]
occupied = [s for s in slots if s["status"] == "occupied"]
reserved = [s for s in slots if s["status"] == "reserved"]

# Top Metrics Row
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Capacity", total, "4 Zones")
c2.metric("Available Spaces", len(available), f"{len(available)/total*100:.1f}% Free", delta_color="normal")
c3.metric("Occupied Spaces", len(occupied), f"{len(occupied)/total*100:.1f}% Parked", delta_color="inverse")
c4.metric("Active Reservations", len(reserved), f"{len(reserved)/total*100:.1f}% Held")

st.divider()

# Interactive Parking Lot Grid
st.markdown("### 🚘 Live Parking Space Grid")
st.caption("Green = Available | Red = Occupied | Yellow = Reserved")

zones = ["Zone A", "Zone B", "Zone C", "Zone D"]

for zone in zones:
    st.markdown(f"#### {zone}")
    zone_slots = [s for s in slots if s["zone"] == zone]
    cols = st.columns(6)
    
    for i, s in enumerate(zone_slots):
        slot_id = s["slot_id"]
        status = s["status"]
        price = s["hourly_price"]
        dist = s["distance_m"]
        has_ev = "⚡" if s["has_ev"] else ""
        is_acc = "♿" if s["is_accessible"] else ""
        
        if status == "available":
            badge_class = "badge-available"
            status_symbol = "🟢 Free"
        elif status == "occupied":
            badge_class = "badge-occupied"
            status_symbol = "🔴 Occupied"
        else:
            badge_class = "badge-reserved"
            status_symbol = "🟡 Reserved"
            
        with cols[i % 6]:
            st.markdown(f"""
            <div style="background:#1E293B; border:1px solid #334155; border-radius:10px; padding:12px; text-align:center;">
                <div style="font-weight:700; font-size:1.1rem; color:#F8FAFC;">{slot_id} {has_ev}{is_acc}</div>
                <div style="margin:6px 0;"><span class="{badge_class}">{status_symbol}</span></div>
                <div style="font-size:0.78rem; color:#94A3B8;">₹{price:.0f}/hr | {dist}m</div>
            </div>
            """, unsafe_allow_html=True)

st.divider()

# Bottom Row: Analytics & Recent Events
col_left, col_right = st.columns([3, 2])

with col_left:
    st.markdown("### 📈 Status Distribution")
    fig_pie = analytics_engine.create_occupancy_pie_chart(slots)
    st.plotly_chart(fig_pie, use_container_width=True)

with col_right:
    st.markdown("### 📜 Recent System Events")
    events = db_manager.get_events(limit=8)
    if events:
        for ev in events:
            st.markdown(f"• **`[{ev['timestamp']}]`** Slot `{ev['slot_id'] or 'SYS'}` — {ev['details']}")
    else:
        st.info("No system events recorded yet.")
