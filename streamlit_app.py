import os
import io
import time
from datetime import datetime, date
import numpy as np
from PIL import Image
import streamlit as st

# Ensure Flask app and models are in path
from config import Config
from app import app
from database.models import db, ParkingSlot, ParkingSession, Guard, Alert, SimulationEvent, RecognitionLog
from database.database import init_db
from services.allocation_service import AllocationService
from services.session_service import SessionService
from services.parking_service import ParkingService
from services.pricing_service import PricingService
from services.billing_service import BillingService
from services.alert_service import AlertService

# ANPR imports — optional (heavy ML packages may not be available on cloud)
ANPR_AVAILABLE = False
try:
    from anpr.camera import CameraUtils
    from anpr.recognition_pipeline import ANPRPipeline
    ANPR_AVAILABLE = True
except ImportError:
    CameraUtils = None
    ANPRPipeline = None

# Streamlit Page Config
st.set_page_config(
    page_title="SmartPark AI — Intelligent Facility Simulator",
    page_icon="🅿️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for dark theme, parking bay status colors, and card aesthetics
st.markdown("""
<style>
  .metric-card {
    background-color: #1e293b;
    border: 1px solid #334155;
    border-radius: 10px;
    padding: 1rem;
    text-align: center;
  }
  .slot-badge-vacant { background-color: #052e16; color: #4ade80; border: 1px solid #22c55e; padding: 2px 8px; border-radius: 6px; font-weight: bold; }
  .slot-badge-reserved { background-color: #422006; color: #fde047; border: 1px solid #eab308; padding: 2px 8px; border-radius: 6px; font-weight: bold; }
  .slot-badge-occupied { background-color: #450a0a; color: #f87171; border: 1px solid #ef4444; padding: 2px 8px; border-radius: 6px; font-weight: bold; }
  .slot-badge-blocked { background-color: #1e293b; color: #94a3b8; border: 1px solid #64748b; padding: 2px 8px; border-radius: 6px; font-weight: bold; }
  
  .digital-ticket {
    background: linear-gradient(135deg, #1e293b, #0f172a);
    border: 2px dashed #38bdf8;
    border-radius: 12px;
    padding: 1.5rem;
    margin-top: 1rem;
  }
</style>
""", unsafe_allow_html=True)

# Initialize Flask/SQLAlchemy database context + seed default data
with app.app_context():
    init_db(app)

# Cache pipeline instance in session state (only if ANPR packages are installed)
if "anpr_pipeline" not in st.session_state:
    if ANPR_AVAILABLE:
        st.session_state.anpr_pipeline = ANPRPipeline()
    else:
        st.session_state.anpr_pipeline = None

# Helper function to get summary
def get_summary():
    with app.app_context():
        return AllocationService.get_availability_summary()

# Sidebar Navigation
st.sidebar.image("https://img.icons8.com/fluency/96/parking.png", width=64)
st.sidebar.title("SmartPark AI")
st.sidebar.markdown("**Intelligent Facility Simulator**")

nav_choice = st.sidebar.radio(
    "Facility Interface Portals:",
    [
        "🏠 Portal Home",
        "🚗 Driver Entry Machine (Interface 1)",
        "🅿️ Parking Area Monitoring (Interface 2)",
        "🛡️ Guard Operations Dashboard (Interface 3)",
        "🚪 Driver Exit Machine (Interface 4)"
    ]
)

# Sidebar Facility Status Summary
summary = get_summary()
st.sidebar.markdown("---")
st.sidebar.markdown("### 📊 Facility Capacity")
c1, c2 = st.sidebar.columns(2)
c1.metric("🟢 Vacant", summary["vacant"])
c2.metric("🟡 Reserved", summary["reserved"])
c3, c4 = st.sidebar.columns(2)
c3.metric("🔴 Occupied", summary["occupied"])
c4.metric("⚪ Blocked", summary["blocked"])

st.sidebar.markdown("---")
st.sidebar.markdown("💡 *Local AI-powered parking simulator & dynamic billing engine.*")

# ==========================================================
# 1. PORTAL HOME
# ==========================================================
if nav_choice == "🏠 Portal Home":
    st.title("🅿️ SmartPark AI Intelligent Parking Facility")
    st.markdown("Locally running, end-to-end AI-powered parking management system. Features Automatic Number Plate Recognition (ANPR), category-compatible allocation, live facility state synchronization, IoT incident simulation, and snapshot-based dynamic billing.")

    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.info(f"### 🟢 {summary['vacant']} VACANT\nReady for Allocation")
    with col2:
        st.warning(f"### 🟡 {summary['reserved']} RESERVED\nEn Route to Bay")
    with col3:
        st.error(f"### 🔴 {summary['occupied']} OCCUPIED\nActively Parked")
    with col4:
        st.markdown(f"<div class='metric-card'><h3>⚪ {summary['blocked']} BLOCKED</h3>Obstruction / Incident</div>", unsafe_allow_html=True)

    st.markdown("### 🚀 Unified Facility Interfaces")
    i1, i2 = st.columns(2)
    with i1:
        with st.container(border=True):
            st.markdown("#### 🚗 Interface 1: Driver Entry Machine")
            st.write("Automated kiosk at facility entry gate. Opens camera, detects number plate with YOLO, performs OCR text recognition, checks category availability, and issues a reserved parking ticket.")
        with st.container(border=True):
            st.markdown("#### 🛡️ Interface 3: Guard Operations Console")
            st.write("Control room console for management staff. Live operational metrics, security alerts acknowledgement & resolution, recent entry/exit audit logs, and dynamic category-specific pricing configuration.")
    with i2:
        with st.container(border=True):
            st.markdown("#### 🅿️ Interface 2: Parking Area Monitoring")
            st.write("Visual real-time interactive parking lot grid. Displays Disabled, EV Charging, and Normal parking slots with instant color feedback and full simulation control scenarios.")
        with st.container(border=True):
            st.markdown("#### 🚪 Interface 4: Driver Exit Machine")
            st.write("Automated exit terminal. Recognizes the departing vehicle via webcam ANPR, identifies its active session, computes parking duration from actual parking start time, applies saved pricing rules, and releases the slot.")

# ==========================================================
# 2. DRIVER ENTRY MACHINE (INTERFACE 1)
# ==========================================================
elif nav_choice == "🚗 Driver Entry Machine (Interface 1)":
    st.title("🚗 Driver Entry Machine")
    st.caption("Entry Gate Kiosk — Automated Number Plate Detection & Allocation")

    left_col, right_col = st.columns([1.1, 1], gap="large")

    with left_col:
        st.subheader("📷 Entry Camera & ANPR Scanner")
        
        # Camera options: Camera input or file upload
        scan_mode = st.radio("Input Source:", ["Live Webcam", "Upload Image", "Instant Demo Test Plate"], horizontal=True)
        
        input_image = None
        if scan_mode == "Live Webcam":
            cam_pic = st.camera_input("Capture Vehicle Number Plate")
            if cam_pic:
                input_image = Image.open(cam_pic).convert("RGB")
        elif scan_mode == "Upload Image":
            up_file = st.file_uploader("Upload Vehicle Plate Image", type=["jpg", "jpeg", "png"])
            if up_file:
                input_image = Image.open(up_file).convert("RGB")
        else:
            st.markdown("**⚡ Select an Indian Demo Benchmark Plate:**")
            demo_cols = st.columns(4)
            demo_plates = [
                ("DL01AB1234", "Normal Parking"),
                ("MH02EV1001", "EV Charging Parking"),
                ("KA05MG8821", "Disabled Parking"),
                ("22BH1029AB", "Normal Parking")
            ]
            for idx, (p, cat) in enumerate(demo_plates):
                if demo_cols[idx].button(f"{p}\n({cat.split()[0]})", key=f"demo_btn_{idx}"):
                    st.session_state["entry_reg"] = p
                    st.session_state["entry_cat"] = cat
                    st.success(f"Selected demo plate: **{p}** ({cat})")

        # Process Image with ANPR
        if input_image is not None:
            st.image(input_image, caption="Captured Entry Frame", use_container_width=True)
            
            if st.session_state.anpr_pipeline is not None:
                bgr_frame = np.array(input_image)[:, :, ::-1]
                with st.spinner("Running YOLO Plate Detection & OCR..."):
                    with app.app_context():
                        anpr_res = st.session_state.anpr_pipeline.process_frame(bgr_frame, gate_type="entry")
                
                if anpr_res.get("success"):
                    reg = anpr_res.get("registration_number") or anpr_res.get("raw_text")
                    st.session_state["entry_reg"] = reg
                    conf_tier = anpr_res.get("confidence_tier", "MEDIUM")
                    combined_conf = anpr_res.get("combined_confidence", 0.0)
                    
                    if anpr_res.get("cropped_plate_b64"):
                        st.markdown("#### 🔍 Extracted Number Plate")
                        st.image(anpr_res["cropped_plate_b64"], caption=f"Extracted Crop (Confidence: {combined_conf*100:.1f}%)", width=240)
                    
                    if conf_tier == "HIGH":
                        st.success(f"✅ High-Confidence Plate Recognized: **{reg}** ({combined_conf*100:.1f}%)")
                    else:
                        st.warning(f"⚠️ Plate Detected: **{reg}** ({conf_tier} - {combined_conf*100:.1f}%). Please confirm.")
            else:
                st.info("📷 Image captured. ANPR engine not available on cloud — please type the registration number manually in the right panel.")

    with right_col:
        st.subheader("📋 Parking Slot Allocation")
        
        default_reg = st.session_state.get("entry_reg", "")
        reg_input = st.text_input("VEHICLE REGISTRATION NUMBER", value=default_reg, placeholder="e.g. DL01AB1234").strip().upper()
        
        # Category Availability Display
        by_cat = summary["by_category"]
        cat_options = [
            f"Disabled Parking ({by_cat['Disabled Parking']['vacant']} vacant)",
            f"EV Charging Parking ({by_cat['EV Charging Parking']['vacant']} vacant)",
            f"Normal Parking ({by_cat['Normal Parking']['vacant']} vacant)"
        ]
        
        default_cat_index = 2
        if st.session_state.get("entry_cat") == "Disabled Parking": default_cat_index = 0
        elif st.session_state.get("entry_cat") == "EV Charging Parking": default_cat_index = 1
        
        selected_cat_str = st.radio("SELECT PARKING CATEGORY", cat_options, index=default_cat_index)
        selected_category = selected_cat_str.split(" (")[0]
        
        if st.button("🎟️ Confirm & Allocate Slot", type="primary", use_container_width=True):
            if not reg_input:
                st.error("Please enter or scan a vehicle registration number.")
            else:
                with app.app_context():
                    alloc_res = AllocationService.allocate_slot(reg_input, selected_category)
                
                if alloc_res.get("success"):
                    sess = alloc_res["session"]
                    slot = alloc_res["slot"]
                    st.session_state["last_ticket"] = (sess, slot)
                    st.success(f"🎉 Success! Slot **{slot['slot_number']}** reserved for {reg_input} under Ticket **#{sess['ticket_id']}**.")
                    st.rerun()
                else:
                    st.error(alloc_res.get("error", "Allocation failed."))

        # Display Issued Ticket if exists
        if "last_ticket" in st.session_state:
            sess, slot = st.session_state["last_ticket"]
            st.markdown(f"""
            <div class="digital-ticket">
              <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #334155; padding-bottom:0.5rem; margin-bottom:0.75rem;">
                <span style="font-size:0.85rem; color:#94a3b8;">OFFICIAL ENTRY PASS</span>
                <span style="color:#fde047; font-weight:bold;">{sess['status']}</span>
              </div>
              <div style="display:flex; justify-content:space-between; margin-bottom:0.4rem;">
                <span style="color:#94a3b8;">Ticket ID:</span>
                <strong>{sess['ticket_id']}</strong>
              </div>
              <div style="display:flex; justify-content:space-between; margin-bottom:0.4rem;">
                <span style="color:#94a3b8;">Vehicle Registration:</span>
                <strong style="color:#38bdf8; font-size:1.15rem;">{sess['registration_number']}</strong>
              </div>
              <div style="display:flex; justify-content:space-between; margin-bottom:0.4rem;">
                <span style="color:#94a3b8;">Category:</span>
                <span>{sess['parking_category']}</span>
              </div>
              <div style="display:flex; justify-content:space-between; margin-bottom:0.4rem;">
                <span style="color:#94a3b8;">Assigned Bay:</span>
                <strong style="color:#fde047; font-size:1.35rem;">{slot['slot_number']}</strong>
              </div>
              <div style="display:flex; justify-content:space-between; margin-bottom:0.4rem;">
                <span style="color:#94a3b8;">Entry Time:</span>
                <span>{sess['entry_time']}</span>
              </div>
              <div style="margin-top:0.75rem; font-size:0.8rem; color:#94a3b8; text-align:center;">
                📌 Bay state is RESERVED (Yellow). Billing begins only when physical parking is verified.
              </div>
            </div>
            """, unsafe_allow_html=True)

# ==========================================================
# 3. PARKING AREA MONITORING (INTERFACE 2)
# ==========================================================
elif nav_choice == "🅿️ Parking Area Monitoring (Interface 2)":
    st.title("🅿️ Parking Area Monitoring & Digital Twin")
    st.caption("Real-Time Facility Visual Grid & IoT Incident Simulation Controls")

    with app.app_context():
        slots = ParkingService.get_all_slots()

    # Category Grid Display
    c_dis, c_ev, c_norm = st.columns(3, gap="medium")
    
    with c_dis:
        st.markdown("### ♿ Disabled Parking (D)")
        dis_slots = [s for s in slots if s["category"] == "Disabled Parking"]
        for s in dis_slots:
            st_color = {"VACANT": "🟢", "RESERVED": "🟡", "OCCUPIED": "🔴", "BLOCKED": "⚪"}.get(s["status"], "⚪")
            with st.container(border=True):
                st.markdown(f"**{st_color} Bay {s['slot_number']}** — `{s['status']}`")
                if s.get("registration_number"):
                    st.markdown(f"🚗 Vehicle: **{s['registration_number']}**")
    
    with c_ev:
        st.markdown("### ⚡ EV Charging Parking (E)")
        ev_slots = [s for s in slots if s["category"] == "EV Charging Parking"]
        for s in ev_slots:
            st_color = {"VACANT": "🟢", "RESERVED": "🟡", "OCCUPIED": "🔴", "BLOCKED": "⚪"}.get(s["status"], "⚪")
            with st.container(border=True):
                st.markdown(f"**{st_color} Bay {s['slot_number']}** — `{s['status']}`")
                if s.get("registration_number"):
                    st.markdown(f"🚗 Vehicle: **{s['registration_number']}**")

    with c_norm:
        st.markdown("### 🚗 Normal Parking (N)")
        norm_slots = [s for s in slots if s["category"] == "Normal Parking"]
        for s in norm_slots:
            st_color = {"VACANT": "🟢", "RESERVED": "🟡", "OCCUPIED": "🔴", "BLOCKED": "⚪"}.get(s["status"], "⚪")
            with st.container(border=True):
                st.markdown(f"**{st_color} Bay {s['slot_number']}** — `{s['status']}`")
                if s.get("registration_number"):
                    st.markdown(f"🚗 Vehicle: **{s['registration_number']}**")

    st.markdown("---")
    st.subheader("🕹️ IoT Incident Simulation Controls")
    st.caption("Demonstrate edge-case scenarios and guard alerts live:")

    s1, s2, s3 = st.columns(3)
    with s1:
        with st.container(border=True):
            st.markdown("##### 1. Park Correctly")
            st.caption("Vehicle parks in its reserved space $\\rightarrow$ Turns OCCUPIED and starts billing timer.")
            if st.button("Simulate Correct Park", use_container_width=True):
                with app.app_context():
                    res = ParkingService.simulate_park_correctly()
                if res.get("success"):
                    st.success(f"Vehicle parked in bay {res['slot']['slot_number']}. Timer started!")
                    st.rerun()
                else:
                    st.warning(res.get("error"))

        with st.container(border=True):
            st.markdown("##### 4. Park Incorrectly")
            st.caption("Simulates improper parking alignment; triggers Guard alert.")
            if st.button("Trigger Wrong Parking", use_container_width=True):
                with app.app_context():
                    res = ParkingService.simulate_park_incorrectly(1, "DL01AB9999")
                st.warning("Parking violation alert generated for Guard.")
                st.rerun()

        with st.container(border=True):
            st.markdown("##### 7. Occupy Two Spaces")
            st.caption("Vehicle straddles adjacent bays N-04 and N-05.")
            if st.button("Occupy Bays N-04 & N-05", use_container_width=True):
                with app.app_context():
                    res = ParkingService.simulate_occupy_two_spaces("N-04", "N-05", "KA05GH7890")
                st.error("Critical two-space violation alert sent to Guard.")
                st.rerun()

    with s2:
        with st.container(border=True):
            st.markdown("##### 2. Place Obstacle")
            st.caption("Places cone/debris in a space, marking it BLOCKED.")
            slot_opts = [f"{s['id']}: {s['slot_number']} ({s['status']})" for s in slots if s["status"] != "BLOCKED"]
            if slot_opts:
                sel_slot = st.selectbox("Select Bay to Block:", slot_opts, key="sel_block")
                if st.button("Block Selected Bay", use_container_width=True):
                    slot_id = int(sel_slot.split(":")[0])
                    with app.app_context():
                        ParkingService.simulate_place_object(slot_id, "Maintenance Barrier")
                    st.warning(f"Bay blocked and alert raised.")
                    st.rerun()

        with st.container(border=True):
            st.markdown("##### 5. Block Driving Lane")
            st.caption("Simulates vehicle stalled in transit lane.")
            if st.button("Block Driving Lane A", use_container_width=True):
                with app.app_context():
                    ParkingService.simulate_block_lane("Lane A")
                st.error("Lane blockage critical alert sent to Guard.")
                st.rerun()

        with st.container(border=True):
            st.markdown("##### 8. Wrong Category / Bay")
            st.caption("Vehicle assigned N-01 parks in EV slot E-01.")
            if st.button("Simulate Wrong Bay Parking", use_container_width=True):
                with app.app_context():
                    ParkingService.simulate_wrong_space("N-01", "E-01", "HR26DK8888")
                st.error("Wrong-category parking alert logged.")
                st.rerun()

    with s3:
        with st.container(border=True):
            st.markdown("##### 3. Clear Obstacle")
            st.caption("Removes obstacle and restores bay to valid state.")
            blocked_opts = [f"{s['id']}: {s['slot_number']}" for s in slots if s["status"] == "BLOCKED"]
            if blocked_opts:
                sel_clear = st.selectbox("Select Blocked Bay:", blocked_opts, key="sel_clear")
                if st.button("Clear Obstacle", use_container_width=True):
                    slot_id = int(sel_clear.split(":")[0])
                    with app.app_context():
                        ParkingService.simulate_clear_object(slot_id)
                    st.success("Obstruction cleared. Bay restored.")
                    st.rerun()
            else:
                st.info("No currently blocked bays.")

        with st.container(border=True):
            st.markdown("##### 6. Cross Parking")
            st.caption("Simulates diagonal parking across bay markings.")
            if st.button("Simulate Cross Parking", use_container_width=True):
                with app.app_context():
                    ParkingService.simulate_cross_parking(2, "MH12DE1234")
                st.warning("Cross parking alert generated.")
                st.rerun()

        with st.container(border=True):
            st.markdown("##### 9. Reset Simulation")
            st.caption("Restores all bays to safe VACANT state.")
            if st.button("🔄 Reset All Bays to Vacant", type="primary", use_container_width=True):
                with app.app_context():
                    ParkingService.simulate_reset()
                st.success("All parking bays reset to VACANT.")
                st.rerun()

# ==========================================================
# 4. GUARD DASHBOARD (INTERFACE 3)
# ==========================================================
elif nav_choice == "🛡️ Guard Operations Dashboard (Interface 3)":
    st.title("🛡️ Guard Operations Dashboard")
    st.caption("Facility Control & Security Console | Operator: Duty Guard")

    with app.app_context():
        today_start = datetime.combine(date.today(), datetime.min.time())
        entries_today = ParkingSession.query.filter(ParkingSession.entry_time >= today_start).count()
        exits_today = ParkingSession.query.filter(ParkingSession.exit_time >= today_start, ParkingSession.status == "COMPLETED").count()
        completed_today = ParkingSession.query.filter(ParkingSession.exit_time >= today_start, ParkingSession.status == "COMPLETED").all()
        revenue_today = sum(s.final_amount for s in completed_today)
        open_alerts = Alert.query.filter(Alert.status.in_(["OPEN", "ACKNOWLEDGED"])).all()
        pricing_rules = PricingService.get_all_pricing_rules()
        recent_sessions = ParkingSession.query.order_by(ParkingSession.updated_at.desc()).limit(15).all()

    # KPI row
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total Capacity", f"{summary['total_slots']} Bays", f"{summary['vacant']} Vacant")
    k2.metric("Active Sessions", f"{summary['reserved'] + summary['occupied']}", f"{summary['occupied']} Parked")
    k3.metric("Today's Revenue", f"₹{revenue_today:.2f}", f"{exits_today} Exits Completed")
    k4.metric("Open Alerts", f"{len(open_alerts)}", "Requires Attention", delta_color="inverse")

    st.markdown("---")
    
    # Alerts Table
    st.subheader(f"🚨 Security & Incident Alerts ({len(open_alerts)} Open)")
    if not open_alerts:
        st.info("✅ All systems normal. No active incident alerts.")
    else:
        for al in open_alerts:
            a_col1, a_col2, a_col3 = st.columns([3, 1, 1])
            with a_col1:
                st.markdown(f"**[{al.alert_type}]** — {al.description} *(Severity: {al.severity})*")
                st.caption(f"Created: {al.created_at.strftime('%H:%M:%S')} | Status: `{al.status}`")
            with a_col2:
                if al.status == "OPEN":
                    if st.button("Acknowledge", key=f"ack_{al.id}"):
                        with app.app_context():
                            AlertService.acknowledge_alert(al.id)
                        st.rerun()
            with a_col3:
                if st.button("Resolve", key=f"res_{al.id}", type="primary"):
                    with app.app_context():
                        AlertService.resolve_alert(al.id)
                    st.rerun()
            st.divider()

    st.markdown("---")
    col_p, col_act = st.columns([1, 1], gap="large")

    with col_p:
        st.subheader("💵 Dynamic Category Pricing Rules")
        st.caption("Authorized guards can adjust rates. Active parking sessions retain their initial pricing snapshot.")

        cat_to_edit = st.selectbox("Select Category to Configure:", Config.VALID_CATEGORIES)
        current_rule = next((r for r in pricing_rules if r["category"] == cat_to_edit), None)
        
        if current_rule:
            f_min = st.number_input("Free Duration (Minutes)", min_value=0, value=current_rule["free_minutes"], step=5)
            g_min = st.number_input("Grace Period (Minutes)", min_value=0, value=current_rule["grace_minutes"], step=5)
            r_amt = st.number_input("Charge Rate per Block (₹)", min_value=0.0, value=float(current_rule["charge_amount"]), step=10.0)
            b_int = st.number_input("Billing Block Interval (Minutes)", min_value=15, value=current_rule["billing_interval_minutes"], step=15)
            r_pol = st.selectbox("Rounding Policy", ["CEIL", "FLOOR"], index=0 if current_rule["rounding_policy"] == "CEIL" else 1)

            if st.button("💾 Save Pricing Policy", type="primary", use_container_width=True):
                with app.app_context():
                    PricingService.update_pricing_rule(cat_to_edit, f_min, g_min, r_amt, b_int, r_pol, updated_by="Duty Guard")
                st.success(f"Pricing updated for {cat_to_edit}! Future sessions will use these rates.")
                st.rerun()

    with col_act:
        st.subheader("📋 Recent Vehicle Movements")
        if not recent_sessions:
            st.write("No recorded vehicle movements.")
        else:
            for s in recent_sessions:
                with st.container(border=True):
                    sc1, sc2 = st.columns([2, 1])
                    sc1.markdown(f"**{s.registration_number}** ({s.parking_category})")
                    sc1.caption(f"Slot: {s.slot.slot_number if s.slot else 'N/A'} | Status: `{s.status}`")
                    amt = f"₹{s.final_amount:.2f}" if s.final_amount > 0 else ("Free" if s.status == "COMPLETED" else "In Progress")
                    sc2.markdown(f"### {amt}")

# ==========================================================
# 5. DRIVER EXIT MACHINE (INTERFACE 4)
# ==========================================================
elif nav_choice == "🚪 Driver Exit Machine (Interface 4)":
    st.title("🚪 Driver Exit Machine")
    st.caption("Exit Gate Terminal — Automatic ANPR Recognition & Smart Billing")

    ex_left, ex_right = st.columns([1.1, 1], gap="large")

    with ex_left:
        st.subheader("📷 Exit Camera ANPR Scanner")
        
        ex_mode = st.radio("Exit Scan Mode:", ["Live Webcam", "Upload Image", "Active Parked Vehicles"], horizontal=True)
        
        ex_image = None
        if ex_mode == "Live Webcam":
            ex_cam = st.camera_input("Scan Departing Vehicle Plate")
            if ex_cam:
                ex_image = Image.open(ex_cam).convert("RGB")
        elif ex_mode == "Upload Image":
            ex_up = st.file_uploader("Upload Exit Frame", type=["jpg", "jpeg", "png"], key="exit_upload")
            if ex_up:
                ex_image = Image.open(ex_up).convert("RGB")
        else:
            st.markdown("**⚡ Select an Active Vehicle to Process Exit:**")
            with app.app_context():
                active_sess = ParkingSession.query.filter(ParkingSession.status.in_(["ACTIVE_RESERVED", "ACTIVE_PARKED"])).all()
            if not active_sess:
                st.info("No active vehicle sessions currently in facility.")
            else:
                for asess in active_sess:
                    if st.button(f"🚗 {asess.registration_number} (Bay {asess.slot.slot_number if asess.slot else 'N/A'} - {asess.status})", key=f"btn_exit_{asess.id}"):
                        st.session_state["exit_reg"] = asess.registration_number

        if ex_image is not None:
            st.image(ex_image, caption="Captured Exit Frame", use_container_width=True)
            
            if st.session_state.anpr_pipeline is not None:
                bgr_ex = np.array(ex_image)[:, :, ::-1]
                with st.spinner("Recognizing departing vehicle..."):
                    with app.app_context():
                        ex_res = st.session_state.anpr_pipeline.process_frame(bgr_ex, gate_type="exit")
                
                if ex_res.get("success"):
                    reg = ex_res.get("registration_number") or ex_res.get("raw_text")
                    st.session_state["exit_reg"] = reg
                    st.success(f"Plate scanned: **{reg}**")
            else:
                st.info("📷 Image captured. ANPR engine not available on cloud — please type the registration number manually in the right panel.")

    with ex_right:
        st.subheader("🧾 Active Session & Itemized Bill")
        
        def_ex_reg = st.session_state.get("exit_reg", "")
        lookup_reg = st.text_input("ENTER OR CONFIRM REGISTRATION", value=def_ex_reg).strip().upper()

        if lookup_reg:
            with app.app_context():
                matched_session = SessionService.get_active_session_by_registration(lookup_reg)
                
            if not matched_session:
                st.error(f"No active session found for vehicle **{lookup_reg}**.")
            else:
                with app.app_context():
                    bill_info = BillingService.calculate_bill(matched_session)
                
                # Render itemized bill
                st.markdown(f"""
                <div class="digital-ticket">
                  <div style="display:flex; justify-content:space-between; border-bottom:1px solid #334155; padding-bottom:0.5rem; margin-bottom:0.75rem;">
                    <span style="color:#94a3b8;">SESSION INVOICE: <strong>{matched_session.ticket_id}</strong></span>
                    <span class="slot-badge-{matched_session.status.lower().split('_')[-1]}">{matched_session.status}</span>
                  </div>
                  <div style="display:flex; justify-content:space-between; margin-bottom:0.3rem;">
                    <span>Vehicle Registration:</span>
                    <strong style="color:#38bdf8; font-size:1.15rem;">{matched_session.registration_number}</strong>
                  </div>
                  <div style="display:flex; justify-content:space-between; margin-bottom:0.3rem;">
                    <span>Bay & Category:</span>
                    <strong>{matched_session.slot.slot_number if matched_session.slot else 'N/A'} ({matched_session.parking_category})</strong>
                  </div>
                  <div style="display:flex; justify-content:space-between; margin-bottom:0.3rem;">
                    <span>Parked Start Time:</span>
                    <span>{matched_session.parked_start_time if matched_session.parked_start_time else 'Not Parked (Reserved Only)'}</span>
                  </div>
                  <div style="display:flex; justify-content:space-between; margin-bottom:0.3rem;">
                    <span>Total Parking Duration:</span>
                    <strong>{bill_info['total_duration_minutes']} min</strong>
                  </div>
                  <div style="background:rgba(0,0,0,0.3); border-radius:8px; padding:0.6rem; margin:0.6rem 0;">
                    <div style="display:flex; justify-content:space-between; font-size:0.85rem; margin-bottom:0.2rem;">
                      <span>Free Threshold:</span>
                      <span>{bill_info['free_minutes']}m free + {bill_info['grace_minutes']}m grace ({bill_info['total_free_minutes']}m)</span>
                    </div>
                    <div style="display:flex; justify-content:space-between; font-size:0.85rem; margin-bottom:0.2rem;">
                      <span>Chargeable Duration:</span>
                      <span>{bill_info['chargeable_duration_minutes']} minutes</span>
                    </div>
                    <div style="display:flex; justify-content:space-between; font-size:0.85rem;">
                      <span>Billing Blocks:</span>
                      <span>{bill_info['number_of_blocks']} blocks × ₹{bill_info['rate_per_block']:.2f} / {bill_info['billing_interval_minutes']}m</span>
                    </div>
                  </div>
                  <div style="display:flex; justify-content:space-between; align-items:center; border-top:1px solid #334155; padding-top:0.6rem; margin-top:0.6rem;">
                    <span style="font-size:1.1rem; font-weight:bold;">TOTAL PAYABLE:</span>
                    <strong style="color:#4ade80; font-size:1.8rem;">₹{bill_info['final_amount']:.2f}</strong>
                  </div>
                </div>
                """, unsafe_allow_html=True)

                st.write("")
                b_col1, b_col2 = st.columns([2, 1])
                with b_col1:
                    if st.button("💳 Confirm Exit & Release Bay", type="primary", use_container_width=True):
                        with app.app_context():
                            exit_res = SessionService.process_exit(matched_session.id)
                        if exit_res.get("success"):
                            st.session_state["exit_receipt"] = exit_res
                            st.session_state.pop("exit_reg", None)
                            st.success(f"Exit complete! Bay released to VACANT.")
                            st.rerun()
                        else:
                            st.error(exit_res.get("error"))

                with b_col2:
                    if matched_session.status == "ACTIVE_RESERVED":
                        if st.button("Cancel Reservation", use_container_width=True):
                            with app.app_context():
                                SessionService.cancel_reservation(matched_session.id)
                            st.info("Reservation cancelled without charge. Bay released.")
                            st.rerun()

        # Display Exit Receipt if completed
        if "exit_receipt" in st.session_state:
            rec = st.session_state["exit_receipt"]
            st.markdown(f"""
            <div class="digital-ticket" style="border-color:#22c55e;">
              <h4 style="color:#4ade80; text-align:center;">✅ Payment & Exit Completed</h4>
              <div style="display:flex; justify-content:space-between; margin-bottom:0.3rem;">
                <span>Released Bay:</span>
                <strong style="color:#4ade80;">{rec['slot']['slot_number'] if rec.get('slot') else 'N/A'} (VACANT)</strong>
              </div>
              <div style="display:flex; justify-content:space-between; margin-bottom:0.3rem;">
                <span>Receipt Number:</span>
                <span>{rec['session']['ticket_id']}</span>
              </div>
              <div style="display:flex; justify-content:space-between; margin-bottom:0.3rem;">
                <span>Amount Paid:</span>
                <strong style="color:#4ade80;">₹{rec['session']['final_amount']:.2f}</strong>
              </div>
              <div style="display:flex; justify-content:space-between; margin-bottom:0.3rem;">
                <span>Exit Timestamp:</span>
                <span>{rec['session']['exit_time']}</span>
              </div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("Ready for Next Vehicle", use_container_width=True):
                st.session_state.pop("exit_receipt", None)
                st.rerun()
