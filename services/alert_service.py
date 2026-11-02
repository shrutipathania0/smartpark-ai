"""
Alert and Incident Service for SmartPark AI
Handles incident creation with deduplication, lifecycle transitions
(NEW/OPEN -> IN PROGRESS/ACKNOWLEDGED -> RESOLVED), guard audit, and resolution notes.
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
    """
    Inserts a new alert into the system or updates existing unresolved alert
    to prevent duplicate alerts for the same ongoing incident.
    """
    now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    with get_db() as conn:
        cursor = conn.cursor()

        # Deduplication check: see if matching open/acknowledged incident already exists
        check_query = """
            SELECT id FROM alerts 
            WHERE alert_type = ? AND status IN ('OPEN', 'ACKNOWLEDGED')
        """
        params = [alert_type]

        if slot_id is not None:
            check_query += " AND slot_id = ?"
            params.append(slot_id)
        elif lane_id is not None:
            check_query += " AND lane_id = ?"
            params.append(lane_id)
        elif registration_number is not None:
            check_query += " AND registration_number = ?"
            params.append(registration_number)
        else:
            check_query += " AND slot_id IS NULL AND lane_id IS NULL"

        cursor.execute(check_query, tuple(params))
        existing = cursor.fetchone()

        if existing:
            # Update last_seen_at and description of the ongoing incident
            existing_id = existing[0]
            cursor.execute(
                """UPDATE alerts 
                   SET description = ?, last_seen_at = ? 
                   WHERE id = ?;""",
                (description, now_str, existing_id)
            )
            return existing_id

        # Insert fresh alert
        cursor.execute(
            """INSERT INTO alerts 
               (alert_type, severity, description, registration_number, slot_id, lane_id, status, created_at, last_seen_at) 
               VALUES (?, ?, ?, ?, ?, ?, 'OPEN', ?, ?);""",
            (alert_type, severity, description, registration_number, slot_id, lane_id, now_str, now_str)
        )
        return cursor.lastrowid

def get_alerts(
    status_filter: Optional[str] = None,
    severity_filter: Optional[str] = None,
    search_query: Optional[str] = None,
    sort_by: Optional[str] = "newest",
    limit: int = 100
) -> List[Dict[str, Any]]:
    """
    Retrieves alerts with slot information, supporting multi-criteria filtering,
    search by registration/slot/type, and custom sorting.
    """
    query = """
        SELECT a.*, p.slot_number, p.category as slot_category 
        FROM alerts a 
        LEFT JOIN parking_slots p ON a.slot_id = p.id 
        WHERE 1=1 
    """
    params = []

    # Status filter
    if status_filter and status_filter.upper() != "ALL":
        sf = status_filter.upper()
        if sf == "NEW":
            query += " AND a.status = 'OPEN' "
        elif sf in ("IN_PROGRESS", "IN PROGRESS"):
            query += " AND a.status = 'ACKNOWLEDGED' "
        elif sf == "UNRESOLVED":
            query += " AND a.status IN ('OPEN', 'ACKNOWLEDGED') "
        else:
            query += " AND a.status = ? "
            params.append(sf)

    # Severity filter
    if severity_filter and severity_filter.upper() != "ALL":
        query += " AND a.severity = ? "
        params.append(severity_filter.upper())

    # Text search filter
    if search_query:
        sq = f"%{search_query.strip().upper()}%"
        query += """ AND (
            UPPER(a.alert_type) LIKE ? OR 
            UPPER(a.description) LIKE ? OR 
            UPPER(COALESCE(a.registration_number, '')) LIKE ? OR 
            UPPER(COALESCE(p.slot_number, '')) LIKE ? OR 
            UPPER(COALESCE(a.lane_id, '')) LIKE ?
        ) """
        params.extend([sq, sq, sq, sq, sq])

    # Sorting
    if sort_by == "oldest":
        query += " ORDER BY a.id ASC "
    elif sort_by == "severity":
        query += """ ORDER BY 
            CASE a.severity 
                WHEN 'CRITICAL' THEN 1 
                WHEN 'HIGH' THEN 2 
                WHEN 'MEDIUM' THEN 3 
                ELSE 4 
            END ASC, a.id DESC """
    elif sort_by == "recently_resolved":
        query += " ORDER BY a.resolved_at DESC, a.id DESC "
    else:  # newest first
        query += " ORDER BY a.id DESC "

    query += " LIMIT ?;"
    params.append(limit)

    return query_all(query, tuple(params))

def get_alert_counts() -> Dict[str, int]:
    """Returns summary counts across all alert statuses."""
    all_counts = query_all("""
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN status = 'OPEN' THEN 1 ELSE 0 END) as open_count,
            SUM(CASE WHEN status = 'ACKNOWLEDGED' THEN 1 ELSE 0 END) as in_progress_count,
            SUM(CASE WHEN status = 'RESOLVED' THEN 1 ELSE 0 END) as resolved_count,
            SUM(CASE WHEN severity = 'CRITICAL' AND status IN ('OPEN', 'ACKNOWLEDGED') THEN 1 ELSE 0 END) as critical_unresolved
        FROM alerts;
    """)
    if all_counts and all_counts[0]:
        row = all_counts[0]
        return {
            "total": row["total"] or 0,
            "open": row["open_count"] or 0,
            "in_progress": row["in_progress_count"] or 0,
            "resolved": row["resolved_count"] or 0,
            "critical_unresolved": row["critical_unresolved"] or 0
        }
    return {"total": 0, "open": 0, "in_progress": 0, "resolved": 0, "critical_unresolved": 0}

def acknowledge_alert(alert_id: int, guard_username: Optional[str] = None) -> bool:
    """Marks an alert as IN PROGRESS / ACKNOWLEDGED with timestamp."""
    now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    execute_action(
        """UPDATE alerts 
           SET status = 'ACKNOWLEDGED', acknowledged_at = ? 
           WHERE id = ? AND status = 'OPEN';""",
        (now_str, alert_id)
    )
    return True

def resolve_alert(
    alert_id: int,
    guard_username: Optional[str] = None,
    resolution_note: Optional[str] = None
) -> bool:
    """
    Marks an alert as RESOLVED with resolution timestamp, guard officer,
    and structured confirmation note.
    """
    now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    note = resolution_note.strip() if resolution_note else "Guard confirmed resolution"
    officer = guard_username or "guard_admin"

    execute_action(
        """UPDATE alerts 
           SET status = 'RESOLVED', resolved_at = ?, resolved_by = ?, resolution_note = ? 
           WHERE id = ? AND status IN ('OPEN', 'ACKNOWLEDGED');""",
        (now_str, officer, note, alert_id)
    )
    return True

def record_simulation_event(
    event_type: str,
    slot_id: Optional[int] = None,
    registration_number: Optional[str] = None,
    details: Optional[str] = None
) -> int:
    """Logs simulated parking events for facility audit trail."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO simulation_events (event_type, slot_id, registration_number, details) 
               VALUES (?, ?, ?, ?);""",
            (event_type, slot_id, registration_number, details)
        )
        return cursor.lastrowid
