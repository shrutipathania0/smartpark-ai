import streamlit as st
import config
from database import db_manager
from modules import analytics_engine, reservation_manager

st.set_page_config(page_title="Analytics — SmartPark AI", page_icon="📈", layout="wide")

st.markdown("## 📈 Parking Analytics & Business Intelligence")
st.caption("Real-time occupancy visualizations, historical trend lines, zone performance, and revenue analytics.")

# Fetch Live Data
slots = db_manager.get_all_slots()
history_snapshots = db_manager.get_analytics_history(limit=100)
reservations = db_manager.get_reservations()
res_summary = reservation_manager.get_reservation_summary()

# Top KPI Summary Cards
k1, k2, k3, k4 = st.columns(4)
k1.metric("Total Reservations", res_summary["total_reservations"])
k2.metric("Active Reservations", res_summary["active_reservations"])
k3.metric("Simulated Total Revenue", f"₹{res_summary['total_revenue']:.2f}")
k4.metric("Avg Booking Duration", f"{res_summary['avg_duration_mins']} mins")

st.divider()

# Interactive Chart Grid
st.markdown("### 📊 Real-Time Space Distribution")

c_pie, c_zone = st.columns(2)

with c_pie:
    fig_pie = analytics_engine.create_occupancy_pie_chart(slots)
    st.plotly_chart(fig_pie, use_container_width=True)

with c_zone:
    fig_zone = analytics_engine.create_zone_occupancy_bar_chart(slots)
    st.plotly_chart(fig_zone, use_container_width=True)

st.divider()

st.markdown("### 📉 Historical Performance Trends")

c_occ_time, c_rev_time = st.columns(2)

with c_occ_time:
    fig_occ = analytics_engine.create_occupancy_timeline_chart(history_snapshots)
    st.plotly_chart(fig_occ, use_container_width=True)

with c_rev_time:
    fig_rev = analytics_engine.create_revenue_timeline_chart(history_snapshots)
    st.plotly_chart(fig_rev, use_container_width=True)

st.divider()

st.markdown("### 📑 Reservation Metrics Breakdown")
fig_res = analytics_engine.create_reservation_status_chart(reservations)
st.plotly_chart(fig_res, use_container_width=True)
