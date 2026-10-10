import os
import pathlib

# Base Directory
BASE_DIR = pathlib.Path(__file__).parent.resolve()

# Database Path
DEFAULT_DB_PATH = os.getenv("DB_PATH", str(BASE_DIR / "smartpark.db"))

# Application Metadata
APP_NAME = "SmartPark AI"
APP_TAGLINE = "Next-Gen Intelligent Mobility & Conversational Assistant"
VERSION = "1.0.0"

# Premium Theme Tokens (Dark Navy, Glassmorphism, Neon Indicators)
COLORS = {
    "background": "#0B132B",
    "secondary_bg": "#1C2541",
    "card_bg": "#1E293B",
    "card_border": "#334155",
    "text_primary": "#F8FAFC",
    "text_secondary": "#94A3B8",
    "accent_blue": "#00B4D8",
    "accent_cyan": "#48CAE4",
    "status_available": "#00E676",  # Vibrant Green
    "status_occupied": "#FF5252",   # Vibrant Red
    "status_reserved": "#FFD600",   # Electric Gold / Yellow
    "status_uncertain": "#FF9100",  # Neon Amber
}

# Default Parking Lot Master Data (24 Slots across 4 Zones)
DEFAULT_SLOTS = [
    # Zone A (Near Entrance - Premium / SUV)
    {"slot_id": "A01", "zone": "Zone A", "type": "SUV", "hourly_price": 60, "distance_m": 15, "has_ev": False, "is_accessible": False, "bbox": [50, 50, 150, 120]},
    {"slot_id": "A02", "zone": "Zone A", "type": "SUV", "hourly_price": 60, "distance_m": 18, "has_ev": False, "is_accessible": False, "bbox": [170, 50, 270, 120]},
    {"slot_id": "A03", "zone": "Zone A", "type": "SUV", "hourly_price": 60, "distance_m": 22, "has_ev": False, "is_accessible": False, "bbox": [290, 50, 390, 120]},
    {"slot_id": "A04", "zone": "Zone A", "type": "SUV", "hourly_price": 60, "distance_m": 25, "has_ev": False, "is_accessible": False, "bbox": [410, 50, 510, 120]},
    {"slot_id": "A05", "zone": "Zone A", "type": "Standard", "hourly_price": 50, "distance_m": 30, "has_ev": False, "is_accessible": False, "bbox": [530, 50, 630, 120]},
    {"slot_id": "A06", "zone": "Zone A", "type": "Standard", "hourly_price": 50, "distance_m": 35, "has_ev": False, "is_accessible": False, "bbox": [650, 50, 750, 120]},
    
    # Zone B (Central - Standard / Compact)
    {"slot_id": "B01", "zone": "Zone B", "type": "Standard", "hourly_price": 40, "distance_m": 45, "has_ev": False, "is_accessible": False, "bbox": [50, 160, 150, 230]},
    {"slot_id": "B02", "zone": "Zone B", "type": "Standard", "hourly_price": 40, "distance_m": 48, "has_ev": False, "is_accessible": False, "bbox": [170, 160, 270, 230]},
    {"slot_id": "B03", "zone": "Zone B", "type": "Compact", "hourly_price": 35, "distance_m": 52, "has_ev": False, "is_accessible": False, "bbox": [290, 160, 390, 230]},
    {"slot_id": "B04", "zone": "Zone B", "type": "Compact", "hourly_price": 35, "distance_m": 55, "has_ev": False, "is_accessible": False, "bbox": [410, 160, 510, 230]},
    {"slot_id": "B05", "zone": "Zone B", "type": "Standard", "hourly_price": 40, "distance_m": 60, "has_ev": False, "is_accessible": False, "bbox": [530, 160, 630, 230]},
    {"slot_id": "B06", "zone": "Zone B", "type": "Standard", "hourly_price": 40, "distance_m": 65, "has_ev": False, "is_accessible": False, "bbox": [650, 160, 750, 230]},

    # Zone C (Specialized - EV & Accessible)
    {"slot_id": "C01", "zone": "Zone C", "type": "EV", "hourly_price": 55, "distance_m": 25, "has_ev": True, "is_accessible": False, "bbox": [50, 270, 150, 340]},
    {"slot_id": "C02", "zone": "Zone C", "type": "EV", "hourly_price": 55, "distance_m": 28, "has_ev": True, "is_accessible": False, "bbox": [170, 270, 270, 340]},
    {"slot_id": "C03", "zone": "Zone C", "type": "EV", "hourly_price": 55, "distance_m": 32, "has_ev": True, "is_accessible": False, "bbox": [290, 270, 390, 340]},
    {"slot_id": "C04", "zone": "Zone C", "type": "Accessible", "hourly_price": 30, "distance_m": 12, "has_ev": False, "is_accessible": True, "bbox": [410, 270, 510, 340]},
    {"slot_id": "C05", "zone": "Zone C", "type": "Accessible", "hourly_price": 30, "distance_m": 15, "has_ev": False, "is_accessible": True, "bbox": [530, 270, 630, 340]},
    {"slot_id": "C06", "zone": "Zone C", "type": "EV", "hourly_price": 55, "distance_m": 38, "has_ev": True, "is_accessible": True, "bbox": [650, 270, 750, 340]},

    # Zone D (Economy / North Parking)
    {"slot_id": "D01", "zone": "Zone D", "type": "Compact", "hourly_price": 25, "distance_m": 85, "has_ev": False, "is_accessible": False, "bbox": [50, 380, 150, 450]},
    {"slot_id": "D02", "zone": "Zone D", "type": "Compact", "hourly_price": 25, "distance_m": 90, "has_ev": False, "is_accessible": False, "bbox": [170, 380, 270, 450]},
    {"slot_id": "D03", "zone": "Zone D", "type": "Standard", "hourly_price": 30, "distance_m": 95, "has_ev": False, "is_accessible": False, "bbox": [290, 380, 390, 450]},
    {"slot_id": "D04", "zone": "Zone D", "type": "Standard", "hourly_price": 30, "distance_m": 100, "has_ev": False, "is_accessible": False, "bbox": [410, 380, 510, 450]},
    {"slot_id": "D05", "zone": "Zone D", "type": "SUV", "hourly_price": 35, "distance_m": 110, "has_ev": False, "is_accessible": False, "bbox": [530, 380, 630, 450]},
    {"slot_id": "D06", "zone": "Zone D", "type": "SUV", "hourly_price": 35, "distance_m": 115, "has_ev": False, "is_accessible": False, "bbox": [650, 380, 750, 450]},
]

def get_groq_api_key() -> str:
    """Safely retrieves Groq API key without crashing."""
    try:
        import streamlit as st
        if hasattr(st, "secrets") and "GROQ_API_KEY" in st.secrets:
            return st.secrets["GROQ_API_KEY"]
    except Exception:
        pass
    return os.getenv("GROQ_API_KEY", "")
