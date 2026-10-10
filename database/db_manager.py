import sqlite3
import datetime
import uuid
import os
import pathlib
from typing import List, Dict, Any, Optional
import config

DB_PATH = config.DEFAULT_DB_PATH

def get_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """Creates a sqlite3 connection with dictionary row factory and timeout."""
    target_path = db_path or DB_PATH
    conn = sqlite3.connect(target_path, timeout=10.0)
    conn.row_factory = sqlite3.Row
    # Enable foreign keys
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db(db_path: Optional[str] = None) -> None:
    """Initializes tables and seeds initial slot data if empty."""
    target_path = db_path or DB_PATH
    schema_path = pathlib.Path(__file__).parent / "schema.sql"
    
    with get_connection(target_path) as conn:
        cursor = conn.cursor()
        if schema_path.exists():
            with open(schema_path, "r", encoding="utf-8") as f:
                cursor.executescript(f.read())
        
        # Check if slots exist
        cursor.execute("SELECT COUNT(*) as count FROM slots;")
        count = cursor.fetchone()["count"]
        if count == 0:
            for s in config.DEFAULT_SLOTS:
                cursor.execute("""
                    INSERT INTO slots (slot_id, zone, type, hourly_price, distance_m, has_ev, is_accessible, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 'available');
                """, (
                    s["slot_id"], s["zone"], s["type"], s["hourly_price"],
                    s["distance_m"], 1 if s["has_ev"] else 0, 1 if s["is_accessible"] else 0
                ))
            conn.commit()

def auto_expire_reservations(db_path: Optional[str] = None) -> int:
    """Finds active reservations past their end_time, marks them expired and frees the slots."""
    target_path = db_path or DB_PATH
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    expired_count = 0
    
    with get_connection(target_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT reservation_id, slot_id FROM reservations
            WHERE status = 'active' AND end_time <= ?;
        """, (now_str,))
        expired_rows = cursor.fetchall()
        
        for row in expired_rows:
            res_id = row["reservation_id"]
            slot_id = row["slot_id"]
            
            cursor.execute("UPDATE reservations SET status = 'expired' WHERE reservation_id = ?;", (res_id,))
            cursor.execute("UPDATE slots SET status = 'available', updated_at = CURRENT_TIMESTAMP WHERE slot_id = ?;", (slot_id,))
            cursor.execute("""
                INSERT INTO parking_events (slot_id, event_type, details)
                VALUES (?, 'expiration', ?);
            """, (slot_id, f"Reservation {res_id} expired automatically."))
            expired_count += 1
            
        conn.commit()
    return expired_count

def get_all_slots(db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Returns all slots merged with bounding box definitions from config."""
    target_path = db_path or DB_PATH
    auto_expire_reservations(target_path)
    
    bbox_map = {s["slot_id"]: s.get("bbox", [0, 0, 100, 100]) for s in config.DEFAULT_SLOTS}
    
    with get_connection(target_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM slots ORDER BY slot_id ASC;")
        rows = cursor.fetchall()
        
        results = []
        for r in rows:
            d = dict(r)
            d["has_ev"] = bool(d["has_ev"])
            d["is_accessible"] = bool(d["is_accessible"])
            d["bbox"] = bbox_map.get(d["slot_id"], [0, 0, 100, 100])
            results.append(d)
        return results

def get_slot_by_id(slot_id: str, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Fetches details for a specific slot."""
    target_path = db_path or DB_PATH
    with get_connection(target_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM slots WHERE slot_id = ?;", (slot_id,))
        row = cursor.fetchone()
        if row:
            d = dict(row)
            d["has_ev"] = bool(d["has_ev"])
            d["is_accessible"] = bool(d["is_accessible"])
            return d
        return None

def update_slot_status(slot_id: str, status: str, db_path: Optional[str] = None) -> bool:
    """Updates the status of a specific slot ('available', 'occupied', 'reserved', 'unavailable')."""
    target_path = db_path or DB_PATH
    valid_statuses = {"available", "occupied", "reserved", "unavailable"}
    if status not in valid_statuses:
        raise ValueError(f"Invalid status '{status}'. Must be one of {valid_statuses}")
        
    with get_connection(target_path) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE slots SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE slot_id = ?;", (status, slot_id))
        affected = cursor.rowcount
        if affected > 0:
            cursor.execute("""
                INSERT INTO parking_events (slot_id, event_type, details)
                VALUES (?, 'status_change', ?);
            """, (slot_id, f"Slot status changed to {status}"))
        conn.commit()
        return affected > 0

def create_reservation(
    slot_id: str,
    user_name: str = "Guest User",
    vehicle_type: str = "Sedan",
    vehicle_number: str = "MH-01-AB-1234",
    duration_mins: int = 60,
    db_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Creates a new reservation using double-booking prevention transaction.
    Returns dictionary with result status, message, and reservation details.
    """
    target_path = db_path or DB_PATH
    auto_expire_reservations(target_path)
    
    res_id = f"RES-{uuid.uuid4().hex[:6].upper()}"
    now = datetime.datetime.now()
    end_time = now + datetime.timedelta(minutes=duration_mins)
    
    start_str = now.strftime("%Y-%m-%d %H:%M:%S")
    end_str = end_time.strftime("%Y-%m-%d %H:%M:%S")
    
    with get_connection(target_path) as conn:
        cursor = conn.cursor()
        conn.execute("BEGIN IMMEDIATE;")  # Lock DB for write transaction
        
        cursor.execute("SELECT status, hourly_price FROM slots WHERE slot_id = ?;", (slot_id,))
        slot_row = cursor.fetchone()
        
        if not slot_row:
            conn.rollback()
            return {"success": False, "message": f"Slot {slot_id} does not exist."}
            
        current_status = slot_row["status"]
        if current_status != "available":
            conn.rollback()
            return {"success": False, "message": f"Slot {slot_id} is currently {current_status} and cannot be reserved."}
            
        hourly_price = slot_row["hourly_price"]
        total_price = round((duration_mins / 60.0) * hourly_price, 2)
        
        # Insert reservation
        cursor.execute("""
            INSERT INTO reservations (reservation_id, slot_id, user_name, vehicle_type, vehicle_number, start_time, end_time, duration_mins, total_price, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'active');
        """, (res_id, slot_id, user_name, vehicle_type, vehicle_number, start_str, end_str, duration_mins, total_price))
        
        # Mark slot as reserved
        cursor.execute("UPDATE slots SET status = 'reserved', updated_at = CURRENT_TIMESTAMP WHERE slot_id = ?;", (slot_id,))
        
        # Log event
        cursor.execute("""
            INSERT INTO parking_events (slot_id, event_type, details)
            VALUES (?, 'reservation', ?);
        """, (slot_id, f"Reserved by {user_name} ({res_id}) for {duration_mins} mins."))
        
        conn.commit()
        return {
            "success": True,
            "message": f"Successfully reserved slot {slot_id} for {duration_mins} minutes.",
            "reservation": {
                "reservation_id": res_id,
                "slot_id": slot_id,
                "user_name": user_name,
                "vehicle_type": vehicle_type,
                "vehicle_number": vehicle_number,
                "start_time": start_str,
                "end_time": end_str,
                "duration_mins": duration_mins,
                "total_price": total_price,
                "status": "active"
            }
        }

def cancel_reservation(reservation_id: str, db_path: Optional[str] = None) -> Dict[str, Any]:
    """Cancels an active reservation and frees the slot."""
    target_path = db_path or DB_PATH
    with get_connection(target_path) as conn:
        cursor = conn.cursor()
        conn.execute("BEGIN IMMEDIATE;")
        
        cursor.execute("SELECT slot_id, status FROM reservations WHERE reservation_id = ?;", (reservation_id,))
        res_row = cursor.fetchone()
        
        if not res_row:
            conn.rollback()
            return {"success": False, "message": f"Reservation {reservation_id} not found."}
            
        if res_row["status"] != "active":
            conn.rollback()
            return {"success": False, "message": f"Reservation {reservation_id} is already {res_row['status']}."}
            
        slot_id = res_row["slot_id"]
        cursor.execute("UPDATE reservations SET status = 'cancelled' WHERE reservation_id = ?;", (reservation_id,))
        cursor.execute("UPDATE slots SET status = 'available', updated_at = CURRENT_TIMESTAMP WHERE slot_id = ?;", (slot_id,))
        
        cursor.execute("""
            INSERT INTO parking_events (slot_id, event_type, details)
            VALUES (?, 'cancellation', ?);
        """, (slot_id, f"Reservation {reservation_id} cancelled."))
        
        conn.commit()
        return {"success": True, "message": f"Reservation {reservation_id} cancelled and slot {slot_id} freed."}

def get_reservations(db_path: Optional[str] = None, status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieves reservation history."""
    target_path = db_path or DB_PATH
    auto_expire_reservations(target_path)
    
    with get_connection(target_path) as conn:
        cursor = conn.cursor()
        if status_filter:
            cursor.execute("SELECT * FROM reservations WHERE status = ? ORDER BY created_at DESC;", (status_filter,))
        else:
            cursor.execute("SELECT * FROM reservations ORDER BY created_at DESC;")
        return [dict(r) for r in cursor.fetchall()]

def log_event(event_type: str, slot_id: Optional[str] = None, details: str = "", db_path: Optional[str] = None) -> None:
    """Logs a parking or application event."""
    target_path = db_path or DB_PATH
    with get_connection(target_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO parking_events (slot_id, event_type, details)
            VALUES (?, ?, ?);
        """, (slot_id, event_type, details))
        conn.commit()

def get_events(limit: int = 50, db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Fetches recent parking events."""
    target_path = db_path or DB_PATH
    with get_connection(target_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM parking_events ORDER BY timestamp DESC LIMIT ?;", (limit,))
        return [dict(r) for r in cursor.fetchall()]

def save_analytics_snapshot(
    occupied: int, available: int, reserved: int, total: int, revenue: float = 0.0, db_path: Optional[str] = None
) -> None:
    """Saves a point-in-time snapshot of parking lot analytics."""
    target_path = db_path or DB_PATH
    pct = round((occupied / total) * 100.0, 1) if total > 0 else 0.0
    with get_connection(target_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO analytics_snapshots (occupied_count, available_count, reserved_count, total_slots, occupancy_pct, revenue)
            VALUES (?, ?, ?, ?, ?, ?);
        """, (occupied, available, reserved, total, pct, revenue))
        conn.commit()

def get_analytics_history(limit: int = 100, db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieves analytics history snapshots."""
    target_path = db_path or DB_PATH
    with get_connection(target_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM analytics_snapshots ORDER BY timestamp ASC LIMIT ?;", (limit,))
        return [dict(r) for r in cursor.fetchall()]
