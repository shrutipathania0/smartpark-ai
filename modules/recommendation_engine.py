from typing import List, Dict, Any, Optional

VEHICLE_SLOT_COMPATIBILITY = {
    "SUV": ["SUV", "Standard", "EV"],
    "Sedan": ["Standard", "SUV", "Compact", "EV"],
    "Compact": ["Compact", "Standard", "SUV", "EV"],
    "EV": ["EV", "Standard", "SUV", "Compact"],
    "Motorcycle": ["Compact", "Standard", "SUV", "EV"]
}

def rank_parking_slots(
    slots: List[Dict[str, Any]],
    vehicle_type: str = "Sedan",
    preferred_location: str = "entrance",
    max_hourly_price: Optional[float] = None,
    needs_ev: bool = False,
    needs_accessible: bool = False,
    weight_proximity: float = 0.4,
    weight_price: float = 0.3,
    weight_preference: float = 0.3
) -> List[Dict[str, Any]]:
    """
    Ranks available parking slots according to user constraints and preference weights.
    
    Returns a sorted list of candidate slot dicts with added keys:
    - score: float (0 to 100)
    - explanation: str
    - reasons: list of string rationale
    """
    candidates = []
    
    for slot in slots:
        status = slot.get("status", "available")
        # Step 1: Remove occupied, reserved, or unavailable slots
        if status != "available":
            continue
            
        slot_id = slot["slot_id"]
        slot_type = slot.get("type", "Standard")
        price = slot.get("hourly_price", 40.0)
        dist = slot.get("distance_m", 50)
        has_ev = slot.get("has_ev", False)
        is_accessible = slot.get("is_accessible", False)
        zone = slot.get("zone", "Zone A")
        
        # Step 2: Strict Constraint Filters
        # EV Filter
        if needs_ev and not has_ev:
            continue
            
        # Accessible Filter
        if needs_accessible and not is_accessible:
            continue
            
        # Price Filter
        if max_hourly_price is not None and price > max_hourly_price:
            continue
            
        # Vehicle compatibility filter
        compatible_types = VEHICLE_SLOT_COMPATIBILITY.get(vehicle_type, ["Standard", "SUV", "Compact", "EV", "Accessible"])
        if slot_type not in compatible_types and not is_accessible:
            continue

        # Step 3: Scoring Logic
        # Proximity score (0 to 100): 0m dist -> 100 pts, 120m dist -> 10 pts
        proximity_score = max(0.0, 100.0 - (dist * 0.75))
        
        # Price score (0 to 100): Lower price = higher score relative to 100 cap
        price_score = max(0.0, 100.0 - (price * 1.2))
        if max_hourly_price:
            savings_pct = (max_hourly_price - price) / max_hourly_price
            price_score += max(0.0, savings_pct * 30.0)
            
        # Preference bonus score
        pref_score = 50.0
        reasons = []
        
        # Preferred location matching
        pref_loc_lower = preferred_location.lower()
        if "entrance" in pref_loc_lower and dist <= 30:
            pref_score += 30.0
            reasons.append(f"Close to main entrance ({dist}m)")
        elif "zone a" in pref_loc_lower and "zone a" in zone.lower():
            pref_score += 30.0
            reasons.append("Located in requested Zone A")
        elif "zone b" in pref_loc_lower and "zone b" in zone.lower():
            pref_score += 30.0
            reasons.append("Located in requested Zone B")
        elif "zone c" in pref_loc_lower and "zone c" in zone.lower():
            pref_score += 30.0
            reasons.append("Located in requested Zone C")
        elif "zone d" in pref_loc_lower and "zone d" in zone.lower():
            pref_score += 30.0
            reasons.append("Located in requested Zone D")
        elif "cheap" in pref_loc_lower or "budget" in pref_loc_lower:
            if price <= 35:
                pref_score += 30.0
                reasons.append(f"Budget-friendly price (₹{price:.0f}/hr)")
                
        if vehicle_type.upper() == slot_type.upper():
            pref_score += 15.0
            reasons.append(f"Exact match for {vehicle_type} space")
            
        if has_ev:
            reasons.append("Equipped with EV Fast Charger")
            
        if is_accessible:
            reasons.append("Accessible parking space")
            
        # Weighted total score calculation
        total_score = (
            (proximity_score * weight_proximity) +
            (price_score * weight_price) +
            (pref_score * weight_preference)
        )
        total_score = min(100.0, max(0.0, total_score))
        
        # Build clean explanation
        explanation_summary = f"Slot {slot_id} ({zone}): ₹{price:.0f}/hr, {dist}m from entrance. " + "; ".join(reasons)
        
        candidates.append({
            "slot": slot,
            "slot_id": slot_id,
            "zone": zone,
            "type": slot_type,
            "hourly_price": price,
            "distance_m": dist,
            "has_ev": has_ev,
            "is_accessible": is_accessible,
            "score": round(total_score, 1),
            "reasons": reasons,
            "explanation": explanation_summary
        })
        
    # Sort candidate slots by score descending, then by distance ascending
    candidates.sort(key=lambda x: (-x["score"], x["distance_m"], x["hourly_price"]))
    return candidates
