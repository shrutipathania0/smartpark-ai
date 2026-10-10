import datetime
from typing import Dict, Any, List, Optional
from database import db_manager

def get_all_reservations(status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieves all reservations from DB with auto-expiration check."""
    return db_manager.get_reservations(status_filter=status_filter)

def make_reservation(
    slot_id: str,
    user_name: str,
    vehicle_type: str,
    vehicle_number: str,
    duration_mins: int
) -> Dict[str, Any]:
    """Validates inputs and creates reservation."""
    if not slot_id:
        return {"success": False, "message": "Slot ID is required."}
    if duration_mins <= 0:
        return {"success": False, "message": "Duration must be greater than 0 minutes."}
        
    return db_manager.create_reservation(
        slot_id=slot_id,
        user_name=user_name,
        vehicle_type=vehicle_type,
        vehicle_number=vehicle_number,
        duration_mins=duration_mins
    )

def cancel_existing_reservation(reservation_id: str) -> Dict[str, Any]:
    """Cancels an active reservation."""
    if not reservation_id:
        return {"success": False, "message": "Reservation ID is required."}
    return db_manager.cancel_reservation(reservation_id)

def get_reservation_summary() -> Dict[str, Any]:
    """Generates statistics across all reservation records."""
    all_res = db_manager.get_reservations()
    
    total = len(all_res)
    active = len([r for r in all_res if r["status"] == "active"])
    completed = len([r for r in all_res if r["status"] == "completed"])
    cancelled = len([r for r in all_res if r["status"] == "cancelled"])
    expired = len([r for r in all_res if r["status"] == "expired"])
    
    total_revenue = sum(r["total_price"] for r in all_res if r["status"] in ["active", "completed", "expired"])
    avg_duration = sum(r["duration_mins"] for r in all_res) / total if total > 0 else 0.0
    
    return {
        "total_reservations": total,
        "active_reservations": active,
        "completed_reservations": completed,
        "cancelled_reservations": cancelled,
        "expired_reservations": expired,
        "total_revenue": total_revenue,
        "avg_duration_mins": round(avg_duration, 1)
    }
