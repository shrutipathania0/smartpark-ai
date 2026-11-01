"""
Allocation Service for SmartPark AI
Enforces strict category compatibility, atomic reservation, and duplicate prevention.
"""
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, Tuple
from database.database import get_db
from services.pricing_service import create_pricing_snapshot

VALID_CATEGORIES = ["Disabled Parking", "EV Charging Parking", "Normal Parking"]

def generate_ticket_id() -> str:
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M")
    unique_suffix = uuid.uuid4().hex[:6].upper()
    return f"SPK-{timestamp}-{unique_suffix}"

def check_active_session(registration_number: str) -> Optional[Dict[str, Any]]:
    """Checks if a vehicle already has an active session."""
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
        return dict(row) if row else None

def get_slot_availability() -> Dict[str, Any]:
    """Returns availability counts broken down by category."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """SELECT category, status, COUNT(*) as count 
               FROM parking_slots 
               GROUP BY category, status;"""
        )
        rows = cursor.fetchall()

    summary = {
        "Disabled Parking": {"total": 0, "vacant": 0, "reserved": 0, "occupied": 0, "blocked": 0},
        "EV Charging Parking": {"total": 0, "vacant": 0, "reserved": 0, "occupied": 0, "blocked": 0},
        "Normal Parking": {"total": 0, "vacant": 0, "reserved": 0, "occupied": 0, "blocked": 0},
    }

    for row in rows:
        cat = row["category"]
        stat = row["status"].lower()
        cnt = row["count"]
        if cat in summary:
            summary[cat]["total"] += cnt
            if stat in summary[cat]:
                summary[cat][stat] += cnt

    return summary

def allocate_slot_and_create_ticket(
    registration_number: str,
    parking_category: str
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    Transactionally allocates a compatible vacant slot and creates a parking session + ticket.
    Guarantees:
    1. Valid category check.
    2. Duplicate active session prevention.
    3. Category compatibility (never assigns incompatible category).
    4. Atomic slot lock and status update to 'RESERVED'.
    5. Locks in a pricing snapshot for billing integrity.
    """
    reg = registration_number.strip().upper()
    cat = parking_category.strip()

    if cat not in VALID_CATEGORIES:
        return False, f"Invalid parking category: {cat}. Must be one of {VALID_CATEGORIES}", None

    if not reg:
        return False, "Registration number is required.", None

    with get_db() as conn:
        cursor = conn.cursor()

        # 1. Prevent duplicate active session
        cursor.execute(
            "SELECT id, ticket_id, slot_id FROM parking_sessions WHERE registration_number = ? AND status = 'ACTIVE';",
            (reg,)
        )
        existing = cursor.fetchone()
        if existing:
            return False, f"Vehicle {reg} already has an active parking session (Ticket: {existing['ticket_id']}).", None

        # 2. Find first VACANT slot for the EXACT category
        cursor.execute(
            """SELECT id, slot_number, category, status 
               FROM parking_slots 
               WHERE category = ? AND status = 'VACANT' 
               ORDER BY id ASC LIMIT 1;""",
            (cat,)
        )
        slot = cursor.fetchone()

        if not slot:
            return False, f"No available vacant slots for '{cat}'. All slots in this category are currently reserved, occupied, or blocked.", None

        slot_id = slot["id"]
        slot_number = slot["slot_number"]

        # 3. Create Pricing Snapshot
        pricing_snapshot = create_pricing_snapshot(cat)
        ticket_id = generate_ticket_id()
        now_iso = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

        # 4. Insert Parking Session (status = 'ACTIVE', parked_start_time = None until actually parked)
        cursor.execute(
            """INSERT INTO parking_sessions 
               (ticket_id, registration_number, parking_category, slot_id, entry_time, status, pricing_snapshot) 
               VALUES (?, ?, ?, ?, ?, 'ACTIVE', ?);""",
            (ticket_id, reg, cat, slot_id, now_iso, pricing_snapshot)
        )
        session_id = cursor.lastrowid

        # 5. Update Slot status to RESERVED and set current_session_id
        cursor.execute(
            """UPDATE parking_slots 
               SET status = 'RESERVED', previous_status = 'VACANT', current_session_id = ?, updated_at = CURRENT_TIMESTAMP 
               WHERE id = ?;""",
            (session_id, slot_id)
        )

        # 6. Record Audit Event
        cursor.execute(
            """INSERT INTO parking_events (session_id, event_type, details) 
               VALUES (?, 'TICKET_CREATED', ?);""",
            (session_id, f"Ticket {ticket_id} created for {reg} reserving slot {slot_number}")
        )

        ticket_data = {
            "session_id": session_id,
            "ticket_id": ticket_id,
            "registration_number": reg,
            "parking_category": cat,
            "slot_id": slot_id,
            "slot_number": slot_number,
            "entry_time": now_iso,
            "status": "ACTIVE",
            "slot_status": "RESERVED"
        }

        return True, "Parking slot reserved successfully.", ticket_data

