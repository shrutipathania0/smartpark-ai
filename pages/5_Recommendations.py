import streamlit as st
import config
from database import db_manager
from modules import recommendation_engine
from assets import ui_theme

st.set_page_config(page_title="Recommendations — SmartPark AI", page_icon="🎯", layout="wide")

ui_theme.inject_custom_theme()

st.markdown("""
<div class="smart-banner" style="padding: 20px 28px;">
    <h1>🎯 Intelligent Parking Recommendation Engine</h1>
    <p>Custom multi-criteria ranking algorithm prioritizing proximity, price budget, vehicle size, and special requirements.</p>
</div>
""", unsafe_allow_html=True)

col_f1, col_f2, col_f3 = st.columns(3)

with col_f1:
    vehicle_type = st.selectbox("Vehicle Type", ["Sedan", "SUV", "Compact", "EV", "Motorcycle"], index=0)
    preferred_loc = st.selectbox("Preferred Location", ["entrance", "Zone A", "Zone B", "Zone C", "Zone D", "budget"], index=0)

with col_f2:
    max_price = st.slider("Max Hourly Price (₹/hr)", 20, 100, 60, step=5)
    needs_ev = st.checkbox("⚡ Requires EV Fast Charger")
    needs_acc = st.checkbox("♿ Requires Accessible Space")

with col_f3:
    st.markdown("##### ⚖️ Scoring Weights")
    w_prox = st.slider("Proximity Weight", 0.0, 1.0, 0.4, step=0.1)
    w_price = st.slider("Price Weight", 0.0, 1.0, 0.3, step=0.1)
    w_pref = st.slider("Preference Weight", 0.0, 1.0, 0.3, step=0.1)

st.divider()

slots = db_manager.get_all_slots()
ranked_slots = recommendation_engine.rank_parking_slots(
    slots=slots,
    vehicle_type=vehicle_type,
    preferred_location=preferred_loc,
    max_hourly_price=float(max_price),
    needs_ev=needs_ev,
    needs_accessible=needs_acc,
    weight_proximity=w_prox,
    weight_price=w_price,
    weight_preference=w_pref
)

st.markdown(f"### 📋 Ranked Search Results ({len(ranked_slots)} Matching Available Slots)")

if not ranked_slots:
    st.warning("❌ No available parking spaces match your exact criteria. Try adjusting your max price limit or vehicle requirement.")
else:
    top = ranked_slots[0]
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%); border: 2px solid #00B4D8; border-radius: 16px; padding: 24px; margin-bottom: 24px;">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <h3 style="color:#00B4D8; margin:0;">🏆 Top Recommendation: Slot {top['slot_id']} ({top['zone']})</h3>
            <span style="background:#00B4D8; color:#0B132B; font-weight:800; padding:6px 16px; border-radius:20px; font-size:1.1rem;">Score: {top['score']}/100</span>
        </div>
        <p style="color:#E2E8F0; font-size:1.05rem; margin-top:12px;"><strong>Rationale:</strong> {top['explanation']}</p>
        <div style="display:flex; gap:20px; color:#94A3B8; font-size:0.95rem; margin-top:10px;">
            <span>💰 Rate: <strong>₹{top['hourly_price']:.0f}/hr</strong></span>
            <span>📍 Distance: <strong>{top['distance_m']} meters</strong></span>
            <span>⚡ EV: <strong>{'Yes' if top['has_ev'] else 'No'}</strong></span>
            <span>♿ Accessible: <strong>{'Yes' if top['is_accessible'] else 'No'}</strong></span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    res_col1, res_col2 = st.columns([1, 3])
    with res_col1:
        if st.button(f"📝 Quick Reserve Slot {top['slot_id']}", use_container_width=True):
            res_res = db_manager.create_reservation(slot_id=top['slot_id'], user_name="Guest User", vehicle_type=vehicle_type, duration_mins=60)
            if res_res["success"]:
                st.success(res_res["message"])
                st.rerun()
            else:
                st.error(res_res["message"])

    st.divider()

    st.markdown("#### 🔢 Complete Candidate Ranking Table")
    display_rows = []
    for rank_idx, cand in enumerate(ranked_slots, start=1):
        display_rows.append({
            "Rank": f"#{rank_idx}",
            "Slot ID": cand["slot_id"],
            "Zone": cand["zone"],
            "Slot Type": cand["type"],
            "Match Score": f"{cand['score']} / 100",
            "Price (₹/hr)": cand["hourly_price"],
            "Distance (m)": cand["distance_m"],
            "EV Charger": "⚡ Yes" if cand["has_ev"] else "No",
            "Accessible": "♿ Yes" if cand["is_accessible"] else "No",
            "Explanation": cand["explanation"]
        })
    st.dataframe(display_rows, use_container_width=True)
