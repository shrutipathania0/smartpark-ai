"""
Parking Service for SmartPark AI
Manages slot grids, spatial states, guard analytics, and simulation engine.
"""
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from database.database import get_db, query_all, query_one, execute_action
from services.alert_service import create_alert, record_simulation_event
from services.session_service import record_vehicle_parked

def get_all_slots() -> List[Dict[str, Any]]:
    """Retrieves all parking slots along with session details and active alerts."""
    query = """
        SELECT 
            p.*,
            s.ticket_id,
            s.registration_number,
            s.entry_time,
            s.parked_start_time,
            (SELECT COUNT(*) FROM alerts a WHERE a.slot_id = p.id AND a.status IN ('OPEN', 'ACKNOWLEDGED')) as alert_count
        FROM parking_slots p
        LEFT JOIN parking_sessions s ON p.current_session_id = s.id
        ORDER BY p.id ASC;
    """
    return query_all(query)

def get_slot_detail(slot_id: int) -> Optional[Dict[str, Any]]:
    """Retrieves single slot details with full active session info and alerts."""
    query = """
        SELECT 
            p.*,
            s.ticket_id,
            s.registration_number,
            s.entry_time,
            s.parked_start_time,
            s.status as session_status
        FROM parking_slots p
        LEFT JOIN parking_sessions s ON p.current_session_id = s.id
        WHERE p.id = ?;
    """
    slot = query_one(query, (slot_id,))
    if not slot:
        return None
    slot["alerts"] = query_all(
        "SELECT * FROM alerts WHERE slot_id = ? ORDER BY id DESC LIMIT 5;",
        (slot_id,)
    )
    return slot

def simulate_park_correctly(slot_id: int) -> Tuple[bool, str]:
    """Finds reserved vehicle for this slot and marks it OCCUPIED."""
    slot = query_one("SELECT * FROM parking_slots WHERE id = ?;", (slot_id,))
    if not slot:
        return False, "Slot not found."
    if slot["status"] != "RESERVED" or not slot["current_session_id"]:
        return False, f"Slot {slot['slot_number']} is not currently in RESERVED state."

    success, msg, _ = record_vehicle_parked(slot["current_session_id"])
    record_simulation_event("PARK_CORRECTLY", slot_id, None, msg)
    return success, msg

def simulate_place_object(slot_id: int) -> Tuple[bool, str]:
    """Places an obstruction in slot, setting status to BLOCKED and generating alert."""
    slot = query_one("SELECT * FROM parking_slots WHERE id = ?;", (slot_id,))
    if not slot:
        return False, "Slot not found."
    if slot["status"] == "BLOCKED":
        return False, f"Slot {slot['slot_number']} is already blocked by an object."

    prev_status = slot["status"]
    execute_action(
        """UPDATE parking_slots 
           SET status = 'BLOCKED', previous_status = ?, updated_at = CURRENT_TIMESTAMP 
           WHERE id = ?;""",
        (prev_status, slot_id)
    )

    alert_id = create_alert(
        alert_type="OBJECT_OBSTRUCTION",
        severity="HIGH",
        description=f"Physical object obstruction detected in slot {slot['slot_number']}.",
        slot_id=slot_id
    )
    record_simulation_event("PLACE_OBJECT", slot_id, None, f"Object placed in {slot['slot_number']}. Alert #{alert_id}")
    return True, f"Object placed in slot {slot['slot_number']}. Slot is now BLOCKED."

def simulate_clear_object(slot_id: int) -> Tuple[bool, str]:
    """Clears obstruction from slot, restoring valid previous status safely."""
    slot = query_one("SELECT * FROM parking_slots WHERE id = ?;", (slot_id,))
    if not slot:
        return False, "Slot not found."
    if slot["status"] != "BLOCKED":
        return False, f"Slot {slot['slot_number']} is not blocked."

    # Restore previous status or VACANT if invalid
    restored_status = slot["previous_status"] if slot["previous_status"] in ("VACANT", "RESERVED", "OCCUPIED") else "VACANT"
    
    # If session was cancelled while blocked, don't restore to reserved/occupied
    if restored_status in ("RESERVED", "OCCUPIED") and not slot["current_session_id"]:
        restored_status = "VACANT"

    execute_action(
        """UPDATE parking_slots 
           SET status = ?, previous_status = 'BLOCKED', updated_at = CURRENT_TIMESTAMP 
           WHERE id = ?;""",
        (restored_status, slot_id)
    )

    # Auto-resolve object obstruction alerts for this slot
    execute_action(
        """UPDATE alerts 
           SET status = 'RESOLVED', resolved_at = CURRENT_TIMESTAMP 
           WHERE slot_id = ? AND alert_type = 'OBJECT_OBSTRUCTION' AND status != 'RESOLVED';""",
        (slot_id,)
    )

    record_simulation_event("CLEAR_OBJECT", slot_id, None, f"Object cleared from {slot['slot_number']}, status restored to {restored_status}")
    return True, f"Obstruction cleared. Slot {slot['slot_number']} restored to {restored_status}."

def simulate_park_incorrectly(slot_id: int, vehicle_reg: str = "DL01AB9999") -> Tuple[bool, str]:
    """Generates wrong parking violation without altering underlying session mapping."""
    slot = query_one("SELECT * FROM parking_slots WHERE id = ?;", (slot_id,))
    slot_num = slot["slot_number"] if slot else f"ID-{slot_id}"
    alert_id = create_alert(
        alert_type="WRONG_PARKING",
        severity="MEDIUM",
        description=f"Vehicle {vehicle_reg} parked outside parking lines or overstayed in slot {slot_num}.",
        registration_number=vehicle_reg,
        slot_id=slot_id
    )
    record_simulation_event("PARK_INCORRECTLY", slot_id, vehicle_reg, f"Wrong parking alert #{alert_id}")
    return True, f"Violation logged: Incorrect parking alert created for vehicle {vehicle_reg} in {slot_num}."

def simulate_block_lane(lane_id: str = "Lane A - Entry") -> Tuple[bool, str]:
    """Generates lane blockage alert."""
    alert_id = create_alert(
        alert_type="LANE_BLOCKAGE",
        severity="CRITICAL",
        description=f"Driving lane blockage detected: Traffic stalled at {lane_id}.",
        lane_id=lane_id
    )
    record_simulation_event("BLOCK_LANE", None, None, f"Lane blocked: {lane_id}. Alert #{alert_id}")
    return True, f"Lane obstruction alert triggered for {lane_id}."

def simulate_cross_parking(slot_id: int, vehicle_reg: str = "MH12DE1234") -> Tuple[bool, str]:
    """Simulates cross-parking violation across demarcated parking lines."""
    slot = query_one("SELECT * FROM parking_slots WHERE id = ?;", (slot_id,))
    slot_num = slot["slot_number"] if slot else f"ID-{slot_id}"
    alert_id = create_alert(
        alert_type="CROSS_PARKING",
        severity="HIGH",
        description=f"Vehicle {vehicle_reg} detected cross-parking diagonally over slot {slot_num} line.",
        registration_number=vehicle_reg,
        slot_id=slot_id
    )
    record_simulation_event("CROSS_PARKING", slot_id, vehicle_reg, f"Cross parking in {slot_num}")
    return True, f"Cross parking violation registered for slot {slot_num}."

def simulate_occupy_two_spaces(slot_id_1: int, slot_id_2: int, vehicle_reg: str = "KA03AB5678") -> Tuple[bool, str]:
    """Simulates a vehicle straddling and occupying two spaces."""
    s1 = query_one("SELECT * FROM parking_slots WHERE id = ?;", (slot_id_1,))
    s2 = query_one("SELECT * FROM parking_slots WHERE id = ?;", (slot_id_2,))
    s1_num = s1["slot_number"] if s1 else str(slot_id_1)
    s2_num = s2["slot_number"] if s2 else str(slot_id_2)

    alert_id = create_alert(
        alert_type="TWO_SPACE_OCCUPATION",
        severity="HIGH",
        description=f"Vehicle {vehicle_reg} is straddling and occupying two spaces simultaneously: {s1_num} and {s2_num}.",
        registration_number=vehicle_reg,
        slot_id=slot_id_1
    )
    record_simulation_event("OCCUPY_TWO_SPACES", slot_id_1, vehicle_reg, f"Occupying {s1_num} & {s2_num}")
    return True, f"Violation logged: Vehicle {vehicle_reg} occupies two spaces ({s1_num} and {s2_num})."

def simulate_wrong_space(assigned_slot_id: int, occupied_slot_id: int, vehicle_reg: str) -> Tuple[bool, str]:
    """Simulates vehicle parking in wrong slot, keeping assigned session valid."""
    s_assigned = query_one("SELECT * FROM parking_slots WHERE id = ?;", (assigned_slot_id,))
    s_occ = query_one("SELECT * FROM parking_slots WHERE id = ?;", (occupied_slot_id,))
    assigned_name = s_assigned["slot_number"] if s_assigned else str(assigned_slot_id)
    occ_name = s_occ["slot_number"] if s_occ else str(occupied_slot_id)

    alert_id = create_alert(
        alert_type="WRONG_PARKING",
        severity="HIGH",
        description=f"Vehicle {vehicle_reg} assigned to slot {assigned_name} is detected parked in wrong slot {occ_name}.",
        registration_number=vehicle_reg,
        slot_id=occupied_slot_id
    )
    record_simulation_event("WRONG_SPACE", occupied_slot_id, vehicle_reg, f"Parked in {occ_name} instead of {assigned_name}")
    return True, f"Alert triggered: Vehicle parked in {occ_name} instead of assigned {assigned_name}."

def reset_simulation_environment() -> Tuple[bool, str]:
    """Safely resets parking grid to clean initial state (all slots VACANT, open alerts resolved)."""
    with get_db() as conn:
        cursor = conn.cursor()
        # Cancel any active test sessions
        cursor.execute("UPDATE parking_sessions SET status = 'CANCELLED' WHERE status = 'ACTIVE';")
        # Reset all slots to VACANT
        cursor.execute("UPDATE parking_slots SET status = 'VACANT', previous_status = NULL, current_session_id = NULL, updated_at = CURRENT_TIMESTAMP;")
        # Resolve all alerts
        cursor.execute("UPDATE alerts SET status = 'RESOLVED', resolved_at = CURRENT_TIMESTAMP WHERE status != 'RESOLVED';")
        # Record reset
        cursor.execute("INSERT INTO simulation_events (event_type, details) VALUES ('RESET_SIMULATION', 'Simulation reset to clean baseline.');")

    return True, "Simulation state reset successfully. All slots are now VACANT."

def get_guard_dashboard_stats() -> Dict[str, Any]:
    """Calculates comprehensive guard dashboard analytics."""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Slot status counts
        cursor.execute("SELECT status, COUNT(*) as count FROM parking_slots GROUP BY status;")
        slot_status_counts = {row["status"]: row["count"] for row in cursor.fetchall()}

        # Category occupancy counts
        cursor.execute("""
            SELECT category, 
                   COUNT(*) as total,
                   SUM(CASE WHEN status = 'OCCUPIED' THEN 1 ELSE 0 END) as occupied,
                   SUM(CASE WHEN status = 'RESERVED' THEN 1 ELSE 0 END) as reserved,
                   SUM(CASE WHEN status = 'VACANT' THEN 1 ELSE 0 END) as vacant,
                   SUM(CASE WHEN status = 'BLOCKED' THEN 1 ELSE 0 END) as blocked
            FROM parking_slots 
            GROUP BY category;
        """)
        category_stats = [dict(row) for row in cursor.fetchall()]

        # Active sessions count
        cursor.execute("SELECT COUNT(*) FROM parking_sessions WHERE status = 'ACTIVE';")
        active_sessions = cursor.fetchone()[0]

        # Today's entries
        cursor.execute("SELECT COUNT(*) FROM parking_sessions WHERE date(entry_time) = date('now');")
        today_entries = cursor.fetchone()[0]

        # Today's exits
        cursor.execute("SELECT COUNT(*), COALESCE(SUM(final_amount), 0.0) FROM parking_sessions WHERE status = 'COMPLETED' AND date(exit_time) = date('now');")
        exits_row = cursor.fetchone()
        today_exits = exits_row[0]
        today_revenue = exits_row[1]

        # Open alerts count
        cursor.execute("SELECT COUNT(*) FROM alerts WHERE status IN ('OPEN', 'ACKNOWLEDGED');")
        open_alerts = cursor.fetchone()[0]

    total_slots = sum(slot_status_counts.values())

    return {
        "total_slots": total_slots,
        "vacant_slots": slot_status_counts.get("VACANT", 0),
        "reserved_slots": slot_status_counts.get("RESERVED", 0),
        "occupied_slots": slot_status_counts.get("OCCUPIED", 0),
        "blocked_slots": slot_status_counts.get("BLOCKED", 0),
        "active_sessions": active_sessions,
        "today_entries": today_entries,
        "today_exits": today_exits,
        "today_revenue": round(today_revenue, 2),
        "open_alerts": open_alerts,
        "category_stats": category_stats
    }

