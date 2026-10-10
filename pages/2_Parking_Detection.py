import streamlit as st
import numpy as np
from PIL import Image
import os
import pathlib
import config
from database import db_manager
from modules import vision_detector
from assets import ui_theme

st.set_page_config(page_title="Parking Detection — SmartPark AI", page_icon="📷", layout="wide")

ui_theme.inject_custom_theme()

st.markdown("""
<div class="smart-banner" style="padding: 20px 28px;">
    <h1>📷 Computer Vision Parking Occupancy Detection</h1>
    <p>Detect vehicles, analyze slot occupancy, and visualize status overlays in real-time.</p>
</div>
""", unsafe_allow_html=True)

# Sidebar Settings for Model Weights & Detection Mode
st.sidebar.markdown("### ⚙️ Vision Settings")
use_yolo = st.sidebar.checkbox("Enable YOLO Vehicle Detector", value=True, help="Uses YOLOv8 object detection to locate vehicles.")
yolo_model_path = st.sidebar.text_input("YOLO Weights Path", value="yolov8n.pt")

model_loaded = None
model_msg = "YOLO disabled by user. Operating in CV Edge-Density Fallback Mode."

if use_yolo:
    if st.sidebar.button("⬇️ Download / Load YOLO Weights"):
        with st.spinner("Initializing YOLO model weights..."):
            model_loaded, model_msg = vision_detector.load_yolo_model(yolo_model_path, auto_download=True)
    else:
        model_loaded, model_msg = vision_detector.load_yolo_model(yolo_model_path, auto_download=False)

if use_yolo:
    if model_loaded:
        st.sidebar.success(model_msg)
    else:
        st.sidebar.warning(model_msg)
else:
    st.sidebar.info(model_msg)

# Main UI Tabs
tab_image, tab_manual = st.tabs(["🖼️ Image & Video Upload", "🔧 Manual ROI Slot Config"])

with tab_image:
    st.markdown("### Upload Parking Lot Media")
    
    col_upload, col_sample = st.columns([3, 1])
    uploaded_file = col_upload.file_uploader("Choose a parking lot image (JPG, PNG)", type=["jpg", "png", "jpeg"])
    use_sample = col_sample.button("📷 Load Sample Image", help="Load built-in overhead parking camera sample.")
    
    sample_path = pathlib.Path(__file__).parent.parent / "assets" / "sample_parking.png"
    if not sample_path.exists():
        from assets.generate_sample_assets import create_sample_parking_image
        create_sample_parking_image(str(sample_path))

    input_img = None
    if uploaded_file is not None:
        input_img = Image.open(uploaded_file)
    elif use_sample or "sample_loaded" in st.session_state:
        st.session_state["sample_loaded"] = True
        input_img = Image.open(sample_path)
        
    if input_img is not None:
        st.divider()
        slots_schema = db_manager.get_all_slots()
        
        with st.spinner("Processing computer vision detection pipeline..."):
            res = vision_detector.process_parking_image(
                image_input=input_img,
                slots=slots_schema,
                use_yolo=use_yolo,
                yolo_model=model_loaded
            )
            
        st.markdown(f"#### 🔍 Detection Mode: `{res['mode_label']}`")
        
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Total Slots", res["total_slots"])
        m2.metric("🟢 Vacant", res["vacant_count"], f"{res['vacant_count']/res['total_slots']*100:.0f}%")
        m3.metric("🔴 Occupied", res["occupied_count"], f"{res['occupied_count']/res['total_slots']*100:.0f}%", delta_color="inverse")
        m4.metric("🟡 Uncertain", res["uncertain_count"])
        m5.metric("Occupancy Rate", f"{res['occupancy_pct']}%")
        
        c_orig, c_annot = st.columns(2)
        with c_orig:
            st.image(input_img, caption="Original Input Feed", use_container_width=True)
        with c_annot:
            st.image(res["annotated_image"], caption=f"Occupancy Overlay — {res['mode_label']}", use_container_width=True)
            
        if st.button("🔄 Sync Vision Predictions to Live Database"):
            updated_cnt = 0
            for sr in res["slot_results"]:
                if sr["status"] in ["available", "occupied"]:
                    db_manager.update_slot_status(sr["slot_id"], sr["status"])
                    updated_cnt += 1
            st.success(f"Synced {updated_cnt} slot status predictions to live database!")
            st.rerun()
            
        with st.expander("📋 Detailed Vision Prediction Breakdown"):
            st.dataframe(res["slot_results"], use_container_width=True)
    else:
        st.info("💡 Please upload an image file or click 'Load Sample Image' above to test vision detection.")

with tab_manual:
    st.markdown("### 🔧 Manual Parking Slot ROI Configuration")
    st.write("View and adjust slot bounding box coordinates `[x1, y1, x2, y2]`.")
    slots_list = db_manager.get_all_slots()
    st.dataframe(slots_list, use_container_width=True)
