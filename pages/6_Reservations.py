import streamlit as st
import config
from database import db_manager
from modules import reservation_manager
from assets import ui_theme

st.set_page_config(page_title="Reservations — SmartPark AI", page_icon="📝", layout="wide")

ui_theme.inject_custom_theme()

st.markdown("""
<div class="smart-banner" style="padding: 20px 28px;">
    <h1>📝 Parking Slot Reservation Management</h1>
    <p>Book slots in advance, manage active holds, calculate pricing, and cancel reservations.</p>
</div>
""", unsafe_allow_html=True)

st.info("ℹ️ **Storage Note:** Database records are persisted in local SQLite storage. On ephemeral cloud hosting (Streamlit Cloud), app restarts may reset unbacked DB files.")

tab_book, tab_history, tab_cancel = st.tabs(["➕ New Reservation", "📋 Reservation History", "❌ Cancel Reservation"])

with tab_book:
    st.markdown("### Create New Slot Reservation")
    
    slots = db_manager.get_all_slots()
    avail_slots = [s for s in slots if s["status"] == "available"]
    
    if not avail_slots:
        st.warning("⚠️ All parking slots are currently occupied or reserved. No slots available for booking.")
    else:
        slot_options = [f"{s['slot_id']} ({s['zone']} - {s['type']} - ₹{s['hourly_price']:.0f}/hr)" for s in avail_slots]
        
        col_r1, col_r2 = st.columns(2)
        with col_r1:
            selected_slot_str = st.selectbox("Select Available Slot", slot_options)
            chosen_slot_id = selected_slot_str.split(" ")[0]
            user_name = st.text_input("Customer Name", value="Shruti")
            veh_type = st.selectbox("Vehicle Type", ["Sedan", "SUV", "Compact", "EV", "Motorcycle"], index=0)
            
        with col_r2:
            veh_num = st.text_input("Vehicle License Plate", value="MH-01-AB-1234")
            duration_mins = st.slider("Reservation Duration (Minutes)", 15, 480, 60, step=15)
            
            chosen_slot_obj = next(s for s in avail_slots if s["slot_id"] == chosen_slot_id)
            est_price = (duration_mins / 60.0) * chosen_slot_obj["hourly_price"]
            st.markdown(f"#### Estimated Price: `<span style='color:#00E676;'>₹{est_price:.2f}</span>`", unsafe_allow_html=True)
            
        if st.button("🚀 Confirm Reservation", use_container_width=True):
            res_result = reservation_manager.make_reservation(
                slot_id=chosen_slot_id,
                user_name=user_name,
                vehicle_type=veh_type,
                vehicle_number=veh_num,
                duration_mins=duration_mins
            )
            if res_result["success"]:
                st.balloons()
                st.success(res_result["message"])
                st.json(res_result["reservation"])
                st.rerun()
            else:
                st.error(res_result["message"])

with tab_history:
    st.markdown("### 📋 System Reservation Log")
    status_filter = st.selectbox("Filter Status", ["All", "active", "completed", "cancelled", "expired"], index=0)
    
    filt = None if status_filter == "All" else status_filter
    history = reservation_manager.get_all_reservations(status_filter=filt)
    
    if history:
        st.dataframe(history, use_container_width=True)
    else:
        st.info("No reservation records found for this filter.")

with tab_cancel:
    st.markdown("### ❌ Cancel Existing Reservation")
    
    active_reservations = reservation_manager.get_all_reservations(status_filter="active")
    if not active_reservations:
        st.info("No active reservations found to cancel.")
    else:
        res_opts = [f"{r['reservation_id']} - Slot {r['slot_id']} ({r['user_name']})" for r in active_reservations]
        target_res_str = st.selectbox("Select Active Reservation", res_opts)
        target_res_id = target_res_str.split(" ")[0]
        
        if st.button("⚠️ Confirm Cancellation", use_container_width=True):
            c_res = reservation_manager.cancel_existing_reservation(target_res_id)
            if c_res["success"]:
                st.success(c_res["message"])
                st.rerun()
            else:
                st.error(c_res["message"])
