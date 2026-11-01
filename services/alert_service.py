"""
Alert and Incident Service for SmartPark AI
Handles incident creation, guard alerts, status transitions (OPEN -> ACKNOWLEDGED -> RESOLVED), and audit history.
"""
from datetime import datetime
from typing import List, Dict, Any, Optional
from database.database import get_db, query_all, query_one, execute_action

def create_alert(
    alert_type: str,
    severity: str,
    description: str,
    registration_number: Optional[str] = None,
    slot_id: Optional[int] = None,
    lane_id: Optional[str] = None
) -> int:
    """Inserts a new alert into the system."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO alerts 
               (alert_type, severity, description, registration_number, slot_id, lane_id, status) 
               VALUES (?, ?, ?, ?, ?, ?, 'OPEN');""",
            (alert_type, severity, description, registration_number, slot_id, lane_id)
        )
        return cursor.lastrowid

def get_alerts(status_filter: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
    """Retrieves alerts with related slot information."""
    query = """
        SELECT a.*, p.slot_number, p.category as slot_category 
        FROM alerts a 
        LEFT JOIN parking_slots p ON a.slot_id = p.id 
    """
    params = []
    if status_filter:
        query += " WHERE a.status = ? "
        params.append(status_filter.upper())
    query += " ORDER BY a.id DESC LIMIT ?;"
    params.append(limit)

    return query_all(query, tuple(params))

def acknowledge_alert(alert_id: int) -> bool:
    """Marks an alert as ACKNOWLEDGED."""
    now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    execute_action(
        """UPDATE alerts 
           SET status = 'ACKNOWLEDGED', acknowledged_at = ? 
           WHERE id = ? AND status = 'OPEN';""",
        (now_str, alert_id)
    )
    return True

def resolve_alert(alert_id: int) -> bool:
    """Marks an alert as RESOLVED."""
    now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    execute_action(
        """UPDATE alerts 
           SET status = 'RESOLVED', resolved_at = ? 
           WHERE id = ? AND status IN ('OPEN', 'ACKNOWLEDGED');""",
        (now_str, alert_id)
    )
    return True

def record_simulation_event(
    event_type: str,
    slot_id: Optional[int] = None,
    registration_number: Optional[str] = None,
    details: Optional[str] = None
) -> int:
    """Logs simulated parking events (lane blocked, wrong space, cross park, etc.)."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO simulation_events (event_type, slot_id, registration_number, details) 
               VALUES (?, ?, ?, ?);""",
            (event_type, slot_id, registration_number, details)
        )
        return cursor.lastrowid

