import streamlit as st

def inject_custom_theme():
    """Injects fresh emerald green theme matching mobile smart parking UI."""
    theme_css = """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Outfit:wght@600;700;800&display=swap');
        
        /* Fresh Emerald Green Root Background */
        html, body, [class*="st-"], .stApp, header[data-testid="stHeader"] {
            font-family: 'Plus Jakarta Sans', system-ui, sans-serif !important;
            background: #E8F5E9 !important;
            color: #1F2937 !important;
        }

        header[data-testid="stHeader"] {
            background: #E8F5E9 !important;
        }

        /* Top Emerald Hero Banner */
        .smart-banner {
            background: linear-gradient(135deg, #70C860 0%, #4CAF50 100%) !important;
            border-radius: 24px !important;
            padding: 28px 34px !important;
            color: #FFFFFF !important;
            box-shadow: 0 14px 30px rgba(112, 200, 96, 0.35) !important;
            margin-bottom: 24px !important;
        }
        .smart-banner h1 {
            font-family: 'Outfit', sans-serif !important;
            font-size: 2.5rem !important;
            font-weight: 800 !important;
            color: #FFFFFF !important;
            margin: 0 0 6px 0 !important;
        }
        .smart-banner p {
            color: #F0FDF4 !important;
            font-size: 1.1rem !important;
            margin: 0 !important;
        }

        /* Clean Rounded Floating White Cards */
        .glass-card, .stCard {
            background: #FFFFFF !important;
            border: 1px solid #E5E7EB !important;
            border-radius: 20px !important;
            padding: 20px 24px !important;
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.05) !important;
            margin-bottom: 16px !important;
        }

        /* Simple Visual Parking Bay Cards */
        .bay-card {
            background: #FFFFFF !important;
            border-radius: 18px !important;
            padding: 16px 12px !important;
            text-align: center !important;
            box-shadow: 0 6px 18px rgba(0, 0, 0, 0.04) !important;
            margin-bottom: 10px !important;
            transition: all 0.2s ease !important;
        }
        .bay-card:hover {
            transform: translateY(-3px) !important;
        }
        .bay-available {
            border: 2px solid #4CAF50 !important;
            background: #F0FDF4 !important;
        }
        .bay-occupied {
            border: 2px solid #EF4444 !important;
            background: #FEF2F2 !important;
        }
        .bay-reserved {
            border: 2px solid #F59E0B !important;
            background: #FFFBEB !important;
        }

        /* Sidebar Styling */
        section[data-testid="stSidebar"] {
            background-color: #FFFFFF !important;
            border-right: 1px solid #E5E7EB !important;
        }

        /* Action Buttons - Hot Pink & Emerald Pills */
        div.stButton > button:first-child {
            background: linear-gradient(135deg, #FF2D55 0%, #FF3B30 100%) !important;
            color: #FFFFFF !important;
            border-radius: 30px !important;
            padding: 12px 26px !important;
            font-weight: 700 !important;
            font-family: 'Outfit', sans-serif !important;
            border: none !important;
            box-shadow: 0 6px 18px rgba(255, 45, 85, 0.3) !important;
            transition: all 0.25s ease !important;
        }
        div.stButton > button:first-child:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 8px 24px rgba(255, 45, 85, 0.45) !important;
        }

        /* Streamlit Metric Overrides */
        div[data-testid="stMetricValue"] {
            font-family: 'Outfit', sans-serif !important;
            font-weight: 800 !important;
            color: #1F2937 !important;
        }

        /* Input Fields */
        input, select, textarea {
            border-radius: 16px !important;
            border: 1px solid #D1D5DB !important;
            background: #FFFFFF !important;
            color: #1F2937 !important;
        }
    </style>
    """
    st.markdown(theme_css, unsafe_allow_html=True)
