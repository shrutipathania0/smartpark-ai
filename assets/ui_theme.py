import streamlit as st

def inject_custom_theme():
    """Injects high-end glassmorphism, Google Fonts, and neon animations."""
    theme_css = """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Outfit:wght@500;600;700;800&display=swap');
        
        /* Force Root Background & Font */
        html, body, [class*="st-"], .stApp, header[data-testid="stHeader"] {
            font-family: 'Plus Jakarta Sans', system-ui, sans-serif !important;
            background: #0B132B !important;
            color: #F8FAFC !important;
        }

        /* Top Header Styling */
        header[data-testid="stHeader"] {
            background: #0B132B !important;
        }

        /* Gradient Banner */
        .smart-banner {
            background: linear-gradient(135deg, #1C2541 0%, #0F172A 50%, #00B4D8 100%) !important;
            border: 2px solid #00B4D8 !important;
            padding: 26px 32px !important;
            border-radius: 20px !important;
            margin-bottom: 24px !important;
            box-shadow: 0 12px 30px rgba(0, 180, 216, 0.35) !important;
        }
        .smart-banner h1 {
            font-family: 'Outfit', sans-serif !important;
            font-size: 2.5rem !important;
            font-weight: 800 !important;
            color: #FFFFFF !important;
            margin: 0 0 6px 0 !important;
        }
        .smart-banner p {
            color: #E2E8F0 !important;
            font-size: 1.05rem !important;
            margin: 0 !important;
        }

        /* Glass Cards */
        .glass-card {
            background: rgba(30, 41, 59, 0.85) !important;
            border: 1px solid rgba(0, 180, 216, 0.3) !important;
            border-radius: 16px !important;
            padding: 20px 24px !important;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4) !important;
            margin-bottom: 12px !important;
        }

        /* Visual Parking Bay Styling */
        .bay-card {
            background: #1E293B !important;
            border-radius: 14px !important;
            padding: 16px 12px !important;
            text-align: center !important;
            margin-bottom: 8px !important;
        }
        .bay-available {
            border: 2px solid #00E676 !important;
            background: linear-gradient(180deg, rgba(0, 230, 118, 0.15) 0%, rgba(30, 41, 59, 0.95) 100%) !important;
            box-shadow: 0 0 16px rgba(0, 230, 118, 0.25) !important;
        }
        .bay-occupied {
            border: 2px solid #FF5252 !important;
            background: linear-gradient(180deg, rgba(255, 82, 82, 0.15) 0%, rgba(30, 41, 59, 0.95) 100%) !important;
            box-shadow: 0 0 16px rgba(255, 82, 82, 0.25) !important;
        }
        .bay-reserved {
            border: 2px solid #FFD600 !important;
            background: linear-gradient(180deg, rgba(255, 214, 0, 0.15) 0%, rgba(30, 41, 59, 0.95) 100%) !important;
            box-shadow: 0 0 16px rgba(255, 214, 0, 0.25) !important;
        }

        /* Pulsing Status Dot */
        .pulse-dot {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 6px;
        }
        .dot-green { background: #00E676; box-shadow: 0 0 10px #00E676; }
        .dot-red { background: #FF5252; box-shadow: 0 0 10px #FF5252; }
        .dot-yellow { background: #FFD600; box-shadow: 0 0 10px #FFD600; }

        /* Sidebar Styling */
        section[data-testid="stSidebar"] {
            background-color: #1C2541 !important;
            border-right: 2px solid #1E293B !important;
        }

        /* Tab Buttons Styling */
        button[data-baseweb="tab"] {
            font-family: 'Outfit', sans-serif !important;
            font-size: 1.05rem !important;
            font-weight: 700 !important;
            color: #94A3B8 !important;
        }
        button[aria-selected="true"] {
            color: #00B4D8 !important;
            background: rgba(0, 180, 216, 0.15) !important;
            border-bottom: 3px solid #00B4D8 !important;
        }

        /* Custom Action Buttons */
        div.stButton > button:first-child {
            background: linear-gradient(135deg, #00B4D8 0%, #0077B6 100%) !important;
            color: #FFFFFF !important;
            border: none !important;
            border-radius: 10px !important;
            padding: 10px 22px !important;
            font-weight: 700 !important;
            font-family: 'Outfit', sans-serif !important;
            box-shadow: 0 4px 14px rgba(0, 180, 216, 0.4) !important;
        }
        div.stButton > button:first-child:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 6px 22px rgba(0, 180, 216, 0.6) !important;
            background: linear-gradient(135deg, #48CAE4 0%, #00B4D8 100%) !important;
        }
    </style>
    """
    st.markdown(theme_css, unsafe_allow_html=True)
