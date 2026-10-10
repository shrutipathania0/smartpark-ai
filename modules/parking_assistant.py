import json
from typing import Dict, Any, List, Optional
import config
from database import db_manager
from modules import nlp_processor, recommendation_engine

def process_chat_message(user_message: str, user_name: str = "Guest") -> Dict[str, Any]:
    """
    Main entry point for processing conversational user queries.
    Parses intent/entities, checks live DB state, executes actions, and returns structured & text responses.
    """
    structured_intent = nlp_processor.parse_user_query(user_message)
    intent = structured_intent["intent"]
    
    # Always fetch live slots from Database
    live_slots = db_manager.get_all_slots()
    
    # Dispatch intent handler
    if intent in ["find_parking", "recommend_parking"]:
        response = handle_find_parking(structured_intent, live_slots)
    elif intent == "check_availability":
        response = handle_check_availability(live_slots)
    elif intent == "reserve_parking":
        response = handle_reserve_parking(structured_intent, live_slots, user_name)
    elif intent == "cancel_reservation":
        response = handle_cancel_reservation(structured_intent)
    elif intent == "parking_analytics":
        response = handle_parking_analytics()
    elif intent == "explain_occupancy":
        response = handle_explain_occupancy(live_slots)
    else:
        response = handle_help_intent()
        
    # Optional Groq LLM Enhancement
    groq_api_key = config.get_groq_api_key()
    if groq_api_key:
        enhanced_text = enhance_with_groq(groq_api_key, user_message, response["text_content"], structured_intent)
        if enhanced_text:
            response["text_content"] = enhanced_text
            response["llm_used"] = True
        else:
            response["llm_used"] = False
    else:
        response["llm_used"] = False
        
    response["structured_data"] = structured_intent
    return response

def handle_find_parking(structured: Dict[str, Any], slots: List[Dict[str, Any]]) -> Dict[str, Any]:
    vehicle_type = structured.get("vehicle_type") or "Sedan"
    location = structured.get("preferred_location") or "entrance"
    max_price = structured.get("max_hourly_price")
    needs_ev = structured.get("needs_ev", False)
    needs_accessible = structured.get("needs_accessible", False)
    
    ranked = recommendation_engine.rank_parking_slots(
        slots=slots,
        vehicle_type=vehicle_type,
        preferred_location=location,
        max_hourly_price=max_price,
        needs_ev=needs_ev,
        needs_accessible=needs_accessible
    )
    
    if not ranked:
        text = (
            f"❌ **No suitable parking spaces found** matching your criteria:\n"
            f"- Vehicle: **{vehicle_type}**\n"
            f"- Max Price: **{f'₹{max_price:.0f}/hr' if max_price else 'No Limit'}**\n"
            f"- EV Required: **{'Yes' if needs_ev else 'No'}**\n"
            f"- Accessible Required: **{'Yes' if needs_accessible else 'No'}**\n\n"
            f"💡 *Tip: Try increasing your price budget or searching without zone restrictions.*"
        )
        return {"text_content": text, "recommended_slots": []}
        
    top_picks = ranked[:3]
    top = top_picks[0]
    
    lines = [
        f"🎯 **Top Recommended Parking Slot: `{top['slot_id']}`** (Match Score: **{top['score']}/100**)\n",
        f"- **Zone:** {top['zone']}",
        f"- **Type:** {top['type']}",
        f"- **Hourly Price:** ₹{top['hourly_price']:.0f}/hr",
        f"- **Distance to Entrance:** {top['distance_m']} meters",
        f"- **EV Charging:** {'⚡ Yes' if top['has_ev'] else 'No'}",
        f"- **Accessible:** {'♿ Yes' if top['is_accessible'] else 'No'}\n",
        f"**Why this spot?** {top['explanation']}\n"
    ]
    
    if len(top_picks) > 1:
        lines.append("**Alternative Available Slots:**")
        for alt in top_picks[1:]:
            lines.append(f"• Slot `{alt['slot_id']}` ({alt['zone']}) - ₹{alt['hourly_price']:.0f}/hr, {alt['distance_m']}m away (Score: {alt['score']})")
            
    lines.append(f"\n👉 *Would you like me to reserve **Slot {top['slot_id']}** for you? Simply say 'Reserve slot {top['slot_id']} for 1 hour'.*")
    
    return {
        "text_content": "\n".join(lines),
        "recommended_slots": top_picks
    }

def handle_check_availability(slots: List[Dict[str, Any]]) -> Dict[str, Any]:
    total = len(slots)
    available = [s for s in slots if s["status"] == "available"]
    occupied = [s for s in slots if s["status"] == "occupied"]
    reserved = [s for s in slots if s["status"] == "reserved"]
    
    # Calculate per-zone counts
    zones = {}
    for s in slots:
        z = s["zone"]
        if z not in zones:
            zones[z] = {"total": 0, "available": 0}
        zones[z]["total"] += 1
        if s["status"] == "available":
            zones[z]["available"] += 1
            
    least_crowded_zone = max(zones.items(), key=lambda x: x[1]["available"] / x[1]["total"] if x[1]["total"] > 0 else 0)
    
    lines = [
        f"📊 **Current Parking Lot Availability Summary**\n",
        f"- **Total Spaces:** {total}",
        f"- 🟢 **Available:** {len(available)} ({len(available)/total*100:.1f}%)",
        f"- 🔴 **Occupied:** {len(occupied)} ({len(occupied)/total*100:.1f}%)",
        f"- 🟡 **Reserved:** {len(reserved)} ({len(reserved)/total*100:.1f}%)\n",
        f"**Zone Breakdown:**"
    ]
    
    for z_name, z_data in zones.items():
        lines.append(f"- **{z_name}:** {z_data['available']}/{z_data['total']} free")
        
    lines.append(f"\n💡 **Least Crowded Zone:** `{least_crowded_zone[0]}` ({least_crowded_zone[1]['available']} spaces available)")
    
    return {"text_content": "\n".join(lines)}

def handle_reserve_parking(structured: Dict[str, Any], slots: List[Dict[str, Any]], user_name: str) -> Dict[str, Any]:
    slot_id = structured.get("slot_id")
    duration = structured.get("duration_mins") or 60
    vehicle_type = structured.get("vehicle_type") or "Sedan"
    
    if not slot_id:
        # If user didn't specify slot ID, find top recommendation and suggest/book it
        ranked = recommendation_engine.rank_parking_slots(slots, vehicle_type=vehicle_type)
        if not ranked:
            return {"text_content": "❌ Cannot reserve: No available parking slots match your requirements right now."}
        slot_id = ranked[0]["slot_id"]
        
    res_result = db_manager.create_reservation(
        slot_id=slot_id,
        user_name=user_name,
        vehicle_type=vehicle_type,
        duration_mins=duration
    )
    
    if res_result["success"]:
        res_data = res_result["reservation"]
        text = (
            f"✅ **Reservation Confirmed!**\n\n"
            f"- **Reservation ID:** `{res_data['reservation_id']}`\n"
            f"- **Slot:** `{res_data['slot_id']}`\n"
            f"- **Reserved For:** {res_data['user_name']}\n"
            f"- **Duration:** {duration} minutes\n"
            f"- **Total Price:** ₹{res_data['total_price']:.2f}\n"
            f"- **Valid Until:** {res_data['end_time']}\n\n"
            f"🚗 *Please show this ID at the gate. You can cancel anytime using your Reservation ID.*"
        )
    else:
        text = f"❌ **Reservation Failed:** {res_result['message']}"
        
    return {"text_content": text}

def handle_cancel_reservation(structured: Dict[str, Any]) -> Dict[str, Any]:
    res_id = structured.get("reservation_id")
    
    if not res_id:
        # Fetch active reservations for guest to suggest
        active_res = db_manager.get_reservations(status_filter="active")
        if not active_res:
            return {"text_content": "ℹ️ You have no active reservations to cancel."}
        res_id = active_res[0]["reservation_id"]
        
    cancel_res = db_manager.cancel_reservation(res_id)
    if cancel_res["success"]:
        text = f"✅ **Cancellation Successful!** {cancel_res['message']}"
    else:
        text = f"❌ **Cancellation Failed:** {cancel_res['message']}"
        
    return {"text_content": text}

def handle_parking_analytics() -> Dict[str, Any]:
    events = db_manager.get_events(limit=5)
    reservations = db_manager.get_reservations()
    
    total_rev = sum(r["total_price"] for r in reservations if r["status"] in ["active", "completed", "expired"])
    
    lines = [
        "📈 **SmartPark Analytics Overview**\n",
        f"- **Total Lifetime Reservations:** {len(reservations)}",
        f"- **Total Simulated Revenue:** ₹{total_rev:.2f}",
        f"- **Recent System Activity:**"
    ]
    
    if events:
        for ev in events:
            lines.append(f"  • `[{ev['timestamp']}]` Slot `{ev['slot_id'] or 'SYS'}`: {ev['details']}")
    else:
        lines.append("  • No recent events logged yet.")
        
    return {"text_content": "\n".join(lines)}

def handle_explain_occupancy(slots: List[Dict[str, Any]]) -> Dict[str, Any]:
    total = len(slots)
    occupied = len([s for s in slots if s["status"] == "occupied"])
    reserved = len([s for s in slots if s["status"] == "reserved"])
    occ_pct = (occupied + reserved) / total * 100.0 if total > 0 else 0
    
    reasons = []
    if occ_pct >= 75.0:
        reasons.append("High peak traffic hours in central commercial district.")
        reasons.append("Zone A (Near Entrance) is fully occupied due to convenient access.")
    elif occ_pct >= 40.0:
        reasons.append("Moderate steady traffic across standard slots.")
    else:
        reasons.append("Low overall utilization. Plenty of spaces available across all zones.")
        
    text = (
        f"🔍 **Occupancy Analysis ({occ_pct:.1f}% Capacity Utilized)**\n\n"
        f"- **Occupied Slots:** {occupied}\n"
        f"- **Reserved Slots:** {reserved}\n"
        f"- **Available Slots:** {total - occupied - reserved}\n\n"
        f"**Key Drivers:**\n" + "\n".join([f"• {r}" for r in reasons])
    )
    return {"text_content": text}

def handle_help_intent() -> Dict[str, Any]:
    text = (
        "🤖 **SmartPark Conversational Assistant — Capabilities**\n\n"
        "Here are examples of queries you can ask me:\n"
        "- 🚗 *'Find parking near the entrance for an SUV under ₹60 per hour'* \n"
        "- ⚡ *'Show available EV charging spaces'* \n"
        "- 📊 *'Which parking zone is least crowded?'* \n"
        "- 📝 *'Reserve slot A04 for 45 minutes'* \n"
        "- ❌ *'Cancel my reservation RES-12345'* \n"
        "- 🔍 *'Why is the parking lot almost full?'* \n"
        "- 📈 *'Summarize parking activity and revenue'* \n"
    )
    return {"text_content": text}

def enhance_with_groq(api_key: str, user_prompt: str, base_response: str, structured_intent: Dict[str, Any]) -> Optional[str]:
    """Uses Groq API to polish response into ultra-fluid natural language while retaining exact facts."""
    try:
        from groq import Groq
        client = Groq(api_key=api_key)
        
        sys_prompt = (
            "You are SmartPark AI, an intelligent, helpful, and courteous parking assistant. "
            "Rewrite the factual information provided below into a friendly, professional response. "
            "CRITICAL: Do NOT alter any slot numbers, prices, reservation IDs, or numbers. Keep all facts exact."
        )
        
        user_content = f"User Question: {user_prompt}\nFactual Data:\n{base_response}"
        
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": user_content}
            ],
            temperature=0.3,
            max_tokens=400
        )
        return completion.choices[0].message.content
    except Exception:
        # Fallback to base response if Groq API call fails or key is invalid
        return None
