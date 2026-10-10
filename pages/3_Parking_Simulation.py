import streamlit as st
import time
import config
from database import db_manager
from modules.simulation_engine import ParkingSimulation

st.set_page_config(page_title="Simulation — SmartPark AI", page_icon="🎮", layout="wide")

st.markdown("## 🎮 Interactive Parking & Traffic Simulator")
st.caption("Simulate real-time vehicle arrivals, departures, entrance queuing, and revenue generation.")

# Initialize Simulation in Session State
if "sim" not in st.session_state:
    st.session_state["sim"] = ParkingSimulation()

sim: ParkingSimulation = st.session_state["sim"]

# Top Controls Bar
st.markdown("### 🎛️ Simulation Controls")

ctrl_c1, ctrl_c2, ctrl_c3, ctrl_c4, ctrl_c5 = st.columns(5)

with ctrl_c1:
    if st.button("▶️ Step 1 Cycle", use_container_width=True):
        events = sim.simulate_arrival(1)
        events += sim.simulate_departure(1)
        st.session_state["sim_last_events"] = events

with ctrl_c2:
    if st.button("🚗 +1 Arrival", use_container_width=True):
        events = sim.simulate_arrival(1)
        st.session_state["sim_last_events"] = events

with ctrl_c3:
    if st.button("🚙 +5 Arrivals", use_container_width=True):
        events = sim.simulate_arrival(5)
        st.session_state["sim_last_events"] = events

with ctrl_c4:
    if st.button("👋 -1 Departure", use_container_width=True):
        events = sim.simulate_departure(1)
        st.session_state["sim_last_events"] = events

with ctrl_c5:
    if st.button("🔄 Reset Simulation", use_container_width=True):
        sim.reset()
        st.session_state["sim_last_events"] = ["Simulation reset to initial state."]
        st.rerun()

# Simulation Parameters
st.sidebar.markdown("### ⚙️ Traffic Parameters")
arrival_rate = st.sidebar.slider("Arrival Rate Intensity", 1, 10, 3)
dept_rate = st.sidebar.slider("Departure Probability", 1, 10, 2)

if st.sidebar.button("⏩ Run Auto 5 Steps"):
    all_evts = []
    for _ in range(5):
        ev1 = sim.simulate_arrival(arrival_rate)
        ev2 = sim.simulate_departure(dept_rate)
        all_evts.extend(ev1 + ev2)
    st.session_state["sim_last_events"] = all_evts

st.divider()

# Live Simulation Metrics Summary
summary = sim.get_summary()

m1, m2, m3, m4, m5, m6 = st.columns(6)
m1.metric("Total Slots", summary["total_slots"])
m2.metric("🟢 Free", summary["available_count"])
m3.metric("🔴 Occupied", summary["occupied_count"])
m4.metric("🟡 Reserved", summary["reserved_count"])
m5.metric("⏳ Queue Length", summary["queue_length"], delta=f"{summary['queue_length']} waiting")
m6.metric("💰 Sim Revenue", f"₹{summary['sim_revenue']:.2f}")

st.divider()

# Visual Map Layout of 24 Slots
st.markdown("### 🚥 Live Interactive Parking Grid")

# Group slots by zone
zones = ["Zone A", "Zone B", "Zone C", "Zone D"]
for z in zones:
    st.markdown(f"#### {z}")
    z_slots = [s for s_id, s in sim.slots.items() if s["zone"] == z]
    cols = st.columns(6)
    
    for idx, s in enumerate(z_slots):
        s_id = s["slot_id"]
        status = s["status"]
        
        btn_color = "🟢" if status == "available" else ("🔴" if status == "occupied" else "🟡")
        
        with cols[idx % 6]:
            st.markdown(f"**{s_id}** ({btn_color} `{status}`) - ₹{s['hourly_price']:.0f}")
            new_val = st.selectbox(
                f"Toggle {s_id}",
                ["available", "occupied", "reserved", "unavailable"],
                index=["available", "occupied", "reserved", "unavailable"].index(status),
                key=f"sim_toggle_{s_id}"
            )
            if new_val != status:
                sim.toggle_slot(s_id, new_val)
                st.rerun()

st.divider()

# Simulation Event Logs
st.markdown("### 📜 Simulation Event Stream")
last_events = st.session_state.get("sim_last_events", ["Simulation ready."])
for e in last_events:
    st.markdown(f"• {e}")
