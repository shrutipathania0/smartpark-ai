"""
Session Service for SmartPark AI
Manages full vehicle session lifecycle: reservation, parking, bill preview, exit completion, and cancellation.
"""
from datetime import datetime
from typing import Optional, Dict, Any, Tuple
from database.database import get_db
from services.billing_service import calculate_bill

def get_active_session_by_plate(registration_number: str) -> Optional[Dict[str, Any]]:
    """Retrieves active session for registration number with real-time bill preview."""
    reg = registration_number.strip().upper()
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """SELECT s.*, p.slot_number, p.category as slot_category, p.status as slot_status 
               FROM parking_sessions s 
               JOIN parking_slots p ON s.slot_id = p.id 
               WHERE s.registration_number = ? AND s.status = 'ACTIVE' LIMIT 1;""",
            (reg,)
        )
        row = cursor.fetchone()
        if not row:
            return None
        session = dict(row)

    # Parse timestamps and generate bill preview
    parked_start = None
    if session.get("parked_start_time"):
        try:
            parked_start = datetime.strptime(session["parked_start_time"], "%Y-%m-%d %H:%M:%S")
        except ValueError:
            try:
                parked_start = datetime.fromisoformat(session["parked_start_time"])
            except Exception:
                pass

    now = datetime.utcnow()
    bill_preview = calculate_bill(
        pricing_snapshot_str=session["pricing_snapshot"],
        parked_start_time=parked_start,
        exit_time=now,
        registration_number=session["registration_number"],
        category=session["parking_category"],
        slot_number=session["slot_number"]
    )
    session["bill_preview"] = bill_preview
    return session

def record_vehicle_parked(session_id: int) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """Marks vehicle as parked: RESERVED -> OCCUPIED, records parked_start_time."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """SELECT s.*, p.slot_number, p.status as slot_status 
               FROM parking_sessions s 
               JOIN parking_slots p ON s.slot_id = p.id 
               WHERE s.id = ? AND s.status = 'ACTIVE';""",
            (session_id,)
        )
        session = cursor.fetchone()
        if not session:
            return False, "Active parking session not found.", None

        slot_id = session["slot_id"]
        if session["slot_status"] == "OCCUPIED":
            return True, "Vehicle is already parked in its assigned slot.", dict(session)

        now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute(
            """UPDATE parking_slots 
               SET status = 'OCCUPIED', previous_status = 'RESERVED', updated_at = CURRENT_TIMESTAMP 
               WHERE id = ?;""",
            (slot_id,)
        )

        cursor.execute(
            """UPDATE parking_sessions 
               SET parked_start_time = ?, updated_at = CURRENT_TIMESTAMP 
               WHERE id = ?;""",
            (now_str, session_id)
        )

        cursor.execute(
            """INSERT INTO parking_events (session_id, event_type, details) 
               VALUES (?, 'VEHICLE_PARKED', ?);""",
            (session_id, f"Vehicle parked in slot {session['slot_number']} at {now_str}")
        )

        cursor.execute("SELECT * FROM parking_sessions WHERE id = ?;", (session_id,))
        updated = dict(cursor.fetchone())
        return True, f"Vehicle parked successfully in slot {session['slot_number']}.", updated

def complete_session_and_exit(registration_number: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """Completes the session at exit, settles final bill, releases the slot to VACANT."""
    reg = registration_number.strip().upper()
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """SELECT s.*, p.slot_number, p.status as slot_status 
               FROM parking_sessions s 
               JOIN parking_slots p ON s.slot_id = p.id 
               WHERE s.registration_number = ? AND s.status = 'ACTIVE';""",
            (reg,)
        )
        session = cursor.fetchone()
        if not session:
            return False, f"No active parking session found for registration '{reg}'.", None

        session_id = session["id"]
        slot_id = session["slot_id"]
        now = datetime.utcnow()
        now_str = now.strftime("%Y-%m-%d %H:%M:%S")

        parked_start = None
        if session["parked_start_time"]:
            try:
                parked_start = datetime.strptime(session["parked_start_time"], "%Y-%m-%d %H:%M:%S")
            except ValueError:
                try:
                    parked_start = datetime.fromisoformat(session["parked_start_time"])
                except Exception:
                    pass

        # Final billing calculation
        bill = calculate_bill(
            pricing_snapshot_str=session["pricing_snapshot"],
            parked_start_time=parked_start,
            exit_time=now,
            registration_number=reg,
            category=session["parking_category"],
            slot_number=session["slot_number"]
        )

        final_fee = bill["total_fee"]
        duration_sec = bill.get("duration_seconds", 0)

        # Update Session to COMPLETED
        cursor.execute(
            """UPDATE parking_sessions 
               SET status = 'COMPLETED', exit_time = ?, actual_duration_seconds = ?, 
                   final_amount = ?, updated_at = CURRENT_TIMESTAMP 
               WHERE id = ?;""",
            (now_str, duration_sec, final_fee, session_id)
        )

        # Release slot to VACANT
        cursor.execute(
            """UPDATE parking_slots 
               SET status = 'VACANT', previous_status = ?, current_session_id = NULL, updated_at = CURRENT_TIMESTAMP 
               WHERE id = ?;""",
            (session["slot_status"], slot_id)
        )

        # Record audit event
        cursor.execute(
            """INSERT INTO parking_events (session_id, event_type, details) 
               VALUES (?, 'VEHICLE_EXIT', ?);""",
            (session_id, f"Vehicle exited slot {session['slot_number']}, bill: ₹{final_fee}")
        )

        result = {
            "session_id": session_id,
            "ticket_id": session["ticket_id"],
            "registration_number": reg,
            "slot_number": session["slot_number"],
            "category": session["parking_category"],
            "exit_time": now_str,
            "bill": bill
        }
        return True, f"Exit completed. Slot {session['slot_number']} released to VACANT.", result

