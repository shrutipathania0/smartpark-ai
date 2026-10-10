import streamlit as st
import config

def inject_custom_theme():
    """Injects high-end glassmorphism, Google Fonts, and neon animations."""
    theme_css = """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Outfit:wght@500;600;700;800&display=swap');
        
        /* Base Reset & Fonts */
        html, body, [class*="css"], .stApp {
            font-family: 'Plus Jakarta Sans', system-ui, -apple-system, sans-serif !important;
            background: #0B132B !important;
            color: #F8FAFC !important;
        }

        /* Gradient Main Header Banner */
        .smart-banner {
            background: linear-gradient(135deg, #1C2541 0%, #0F172A 50%, #00B4D8 100%);
            border: 1px solid rgba(72, 202, 228, 0.25);
            padding: 28px 36px;
            border-radius: 20px;
            margin-bottom: 24px;
            box-shadow: 0 15px 30px -10px rgba(0, 180, 216, 0.3);
            position: relative;
            overflow: hidden;
        }
        .smart-banner h1 {
            font-family: 'Outfit', sans-serif !important;
            font-size: 2.5rem !important;
            font-weight: 800 !important;
            color: #FFFFFF !important;
            margin: 0 0 6px 0 !important;
            letter-spacing: -0.02em;
        }
        .smart-banner p {
            color: #E2E8F0 !important;
            font-size: 1.1rem !important;
            margin: 0 !important;
            font-weight: 500;
        }

        /* Glassmorphism Metric Cards */
        .glass-card {
            background: rgba(30, 41, 59, 0.7);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 16px;
            padding: 20px 24px;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
            transition: all 0.3s ease;
        }
        .glass-card:hover {
            transform: translateY(-4px);
            border-color: #00B4D8;
            box-shadow: 0 12px 24px -5px rgba(0, 180, 216, 0.3);
        }

        /* Parking Bay Cards (Visual Lot Grid) */
        .bay-card {
            background: #1E293B;
            border: 2px solid #334155;
            border-radius: 14px;
            padding: 14px 10px;
            text-align: center;
            transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
        }
        .bay-card:hover {
            transform: scale(1.03);
        }
        .bay-available {
            border-color: #00E676;
            background: linear-gradient(180deg, rgba(0, 230, 118, 0.08) 0%, rgba(30, 41, 59, 0.9) 100%);
            box-shadow: 0 0 15px rgba(0, 230, 118, 0.2);
        }
        .bay-occupied {
            border-color: #FF5252;
            background: linear-gradient(180deg, rgba(255, 82, 82, 0.08) 0%, rgba(30, 41, 59, 0.9) 100%);
            box-shadow: 0 0 15px rgba(255, 82, 82, 0.2);
        }
        .bay-reserved {
            border-color: #FFD600;
            background: linear-gradient(180deg, rgba(255, 214, 0, 0.08) 0%, rgba(30, 41, 59, 0.9) 100%);
            box-shadow: 0 0 15px rgba(255, 214, 0, 0.2);
        }

        /* Live Pulsing Indicator Dot */
        .pulse-dot {
            display: inline-block;
            width: 10px;
            height: 10px;
            border-radius: 50%;
            margin-right: 8px;
            animation: pulse-ring 1.8s infinite;
        }
        .dot-green { background: #00E676; box-shadow: 0 0 8px #00E676; }
        .dot-red { background: #FF5252; box-shadow: 0 0 8px #FF5252; }
        .dot-yellow { background: #FFD600; box-shadow: 0 0 8px #FFD600; }

        @keyframes pulse-ring {
            0% { transform: scale(0.95); opacity: 0.9; }
            50% { transform: scale(1.2); opacity: 1; }
            100% { transform: scale(0.95); opacity: 0.9; }
        }

        /* Styled Sidebar */
        section[data-testid="stSidebar"] {
            background-color: #1C2541 !important;
            border-right: 1px solid #1E293B !important;
        }

        /* Streamlit Tabs Styling */
        button[data-baseweb="tab"] {
            font-family: 'Outfit', sans-serif !important;
            font-size: 1.05rem !important;
            font-weight: 600 !important;
            color: #94A3B8 !important;
            border-radius: 10px !important;
            padding: 8px 20px !important;
        }
        button[aria-selected="true"] {
            color: #00B4D8 !important;
            background: rgba(0, 180, 216, 0.12) !important;
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
            letter-spacing: 0.02em;
            box-shadow: 0 4px 14px rgba(0, 180, 216, 0.35);
            transition: all 0.25s ease !important;
        }
        div.stButton > button:first-child:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 6px 20px rgba(0, 180, 216, 0.5) !important;
            background: linear-gradient(135deg, #48CAE4 0%, #00B4D8 100%) !important;
        }
    </style>
    """
    st.markdown(theme_css, unsafe_allow_html=True)
