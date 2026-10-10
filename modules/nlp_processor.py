import re
from typing import Dict, Any, Optional

def parse_user_query(text: str) -> Dict[str, Any]:
    """
    Parses a user natural language query into a structured dict with intent and extracted entities.
    Uses robust regex rules as a reliable offline baseline.
    """
    cleaned = text.strip()
    lower = cleaned.lower()
    
    # Base structure
    structured = {
        "raw_query": cleaned,
        "intent": "help",
        "vehicle_type": None,
        "preferred_location": None,
        "max_hourly_price": None,
        "duration_mins": 60,
        "slot_id": None,
        "reservation_id": None,
        "needs_accessible": False,
        "needs_ev": False
    }
    
    # Entity Extraction
    # 1. Slot ID (e.g. A01, B04, C03, D06)
    slot_match = re.search(r'\b([A-Da-d]0[1-6])\b', cleaned, re.IGNORECASE)
    if slot_match:
        structured["slot_id"] = slot_match.group(1).upper()
        
    # 2. Reservation ID (e.g. RES-A1B2C3)
    res_match = re.search(r'\b(RES-[A-Za-z0-9]+)\b', cleaned, re.IGNORECASE)
    if res_match:
        structured["reservation_id"] = res_match.group(1).upper()
        
    # 3. Vehicle Type
    if "suv" in lower:
        structured["vehicle_type"] = "SUV"
    elif "ev" in lower or "electric" in lower:
        structured["vehicle_type"] = "EV"
        structured["needs_ev"] = True
    elif "compact" in lower or "hatchback" in lower or "small car" in lower:
        structured["vehicle_type"] = "Compact"
    elif "motorcycle" in lower or "bike" in lower or "two wheeler" in lower:
        structured["vehicle_type"] = "Motorcycle"
    elif "sedan" in lower or "car" in lower:
        structured["vehicle_type"] = "Sedan"
        
    # 4. EV & Accessible Flags
    if any(k in lower for k in ["ev", "electric", "charger", "charging"]):
        structured["needs_ev"] = True
    if any(k in lower for k in ["accessible", "handicap", "wheelchair", "disabled"]):
        structured["needs_accessible"] = True
        
    # 5. Price Limit (e.g. under 50, below ₹60, < 40, 50 per hour, 50 rs, 50 rupees)
    price_match = re.search(r'(?:under|below|less than|max|<|₹|\$)?\s*(\d+)\s*(?:rs|rupees|inr|\/hr|per hour|hourly)?', lower)
    # Refined price regex search specifically for context
    price_context = re.search(r'(?:under|below|max|<|budget|price|cost|₹|\$)\s*(\d+)', lower)
    if price_context:
        structured["max_hourly_price"] = float(price_context.group(1))
    elif "under" in lower or "below" in lower or "budget" in lower:
        m = re.search(r'\b(\d+)\b', lower)
        if m:
            structured["max_hourly_price"] = float(m.group(1))

    # 6. Duration (e.g. 30 mins, 30 minutes, 2 hours, 1.5 hrs, 45 m)
    dur_hour_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:hour|hours|hr|hrs)', lower)
    dur_min_match = re.search(r'(\d+)\s*(?:min|mins|minute|minutes)', lower)
    if dur_hour_match:
        structured["duration_mins"] = int(float(dur_hour_match.group(1)) * 60)
    elif dur_min_match:
        structured["duration_mins"] = int(dur_min_match.group(1))
        
    # 7. Preferred Location / Zone
    if "entrance" in lower or "front" in lower or "near door" in lower or "close" in lower:
        structured["preferred_location"] = "entrance"
    elif "zone a" in lower:
        structured["preferred_location"] = "Zone A"
    elif "zone b" in lower:
        structured["preferred_location"] = "Zone B"
    elif "zone c" in lower:
        structured["preferred_location"] = "Zone C"
    elif "zone d" in lower:
        structured["preferred_location"] = "Zone D"
        
    # Intent Detection Classification Rules
    if any(k in lower for k in ["cancel", "unbook", "remove reservation", "revoke"]):
        structured["intent"] = "cancel_reservation"
    elif any(k in lower for k in ["reserve", "book", "hold", "secure"]):
        structured["intent"] = "reserve_parking"
    elif any(k in lower for k in ["recommend", "best spot", "suggest", "which spot"]):
        structured["intent"] = "recommend_parking"
    elif any(k in lower for k in ["find", "search", "look for", "locate", "where can i"]):
        structured["intent"] = "find_parking"
    elif any(k in lower for k in ["available", "open", "free", "vacant", "how many spots", "crowded"]):
        structured["intent"] = "check_availability"
    elif any(k in lower for k in ["analytics", "summary", "report", "stats", "revenue", "entry", "exit", "history"]):
        structured["intent"] = "parking_analytics"
    elif any(k in lower for k in ["why", "reason", "full", "busy", "almost full", "explain"]):
        structured["intent"] = "explain_occupancy"
    elif any(k in lower for k in ["help", "hi", "hello", "what can you do", "commands"]):
        structured["intent"] = "help"
    else:
        # Default fallback intent if search terms are present
        if structured["vehicle_type"] or structured["slot_id"] or structured["preferred_location"]:
            structured["intent"] = "find_parking"
            
    return structured
