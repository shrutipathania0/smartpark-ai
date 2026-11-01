"""
SmartPark AI Database Models and Schema
Shared source of truth for all 4 interfaces (Entry, Monitoring, Guard, Exit).
"""
import sqlite3
import json
from datetime import datetime

DATABASE_PATH = "data/smartpark.db"

def get_db_connection():
    conn = sqlite3.connect(DATABASE_PATH, timeout=20.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Parking Slots
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS parking_slots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        slot_number TEXT UNIQUE NOT NULL,
        category TEXT NOT NULL CHECK(category IN ('Disabled Parking', 'EV Charging Parking', 'Normal Parking')),
        status TEXT NOT NULL CHECK(status IN ('VACANT', 'RESERVED', 'OCCUPIED', 'BLOCKED')),
        previous_status TEXT,
        current_session_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (current_session_id) REFERENCES parking_sessions (id) ON DELETE SET NULL
    );
    """)

    # 2. Parking Sessions
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS parking_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticket_id TEXT UNIQUE NOT NULL,
        registration_number TEXT NOT NULL,
        parking_category TEXT NOT NULL CHECK(parking_category IN ('Disabled Parking', 'EV Charging Parking', 'Normal Parking')),
        slot_id INTEGER NOT NULL,
        entry_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        parked_start_time TIMESTAMP,
        exit_time TIMESTAMP,
        status TEXT NOT NULL CHECK(status IN ('ACTIVE', 'COMPLETED', 'CANCELLED')),
        actual_duration_seconds INTEGER DEFAULT 0,
        final_amount REAL DEFAULT 0.0,
        pricing_snapshot TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (slot_id) REFERENCES parking_slots (id)
    );
    """)

    # 3. Pricing Rules
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS pricing_rules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT UNIQUE NOT NULL CHECK(category IN ('Disabled Parking', 'EV Charging Parking', 'Normal Parking')),
        free_minutes INTEGER NOT NULL DEFAULT 60,
        grace_minutes INTEGER NOT NULL DEFAULT 10,
        charge_amount REAL NOT NULL DEFAULT 50.0,
        billing_interval_minutes INTEGER NOT NULL DEFAULT 120,
        rounding_policy TEXT NOT NULL DEFAULT 'CEIL_INTERVAL',
        updated_by TEXT DEFAULT 'system',
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 4. Guards
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS guards (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 5. Alerts
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        alert_type TEXT NOT NULL,
        severity TEXT NOT NULL CHECK(severity IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
        description TEXT NOT NULL,
        registration_number TEXT,
        slot_id INTEGER,
        lane_id TEXT,
        status TEXT NOT NULL DEFAULT 'OPEN' CHECK(status IN ('OPEN', 'ACKNOWLEDGED', 'RESOLVED')),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        acknowledged_at TIMESTAMP,
        resolved_at TIMESTAMP,
        FOREIGN KEY (slot_id) REFERENCES parking_slots (id)
    );
    """)

    # 6. Simulation Events
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS simulation_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_type TEXT NOT NULL,
        slot_id INTEGER,
        registration_number TEXT,
        details TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (slot_id) REFERENCES parking_slots (id)
    );
    """)

    # 7. Recognition Logs
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS recognition_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        gate_type TEXT NOT NULL CHECK(gate_type IN ('ENTRY', 'EXIT')),
        raw_ocr_text TEXT,
        normalized_registration_number TEXT,
        confidence REAL,
        image_path TEXT,
        recognition_status TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 8. Parking Events (Audit trail)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS parking_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id INTEGER,
        event_type TEXT NOT NULL,
        details TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (session_id) REFERENCES parking_sessions (id)
    );
    """)

    # 9. Indexes for speed and consistency
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_slots_category ON parking_slots(category, status);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_reg_status ON parking_sessions(registration_number, status);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_alerts_status ON alerts(status);")

    # Initial Seed Data: Configure initial slots (3 Disabled, 3 EV, 9 Normal)
    cursor.execute("SELECT COUNT(*) FROM parking_slots;")
    if cursor.fetchone()[0] == 0:
        initial_slots = [
            ("D-01", "Disabled Parking", "VACANT"),
            ("D-02", "Disabled Parking", "VACANT"),
            ("D-03", "Disabled Parking", "VACANT"),
            ("EV-01", "EV Charging Parking", "VACANT"),
            ("EV-02", "EV Charging Parking", "VACANT"),
            ("EV-03", "EV Charging Parking", "VACANT"),
            ("N-01", "Normal Parking", "VACANT"),
            ("N-02", "Normal Parking", "VACANT"),
            ("N-03", "Normal Parking", "VACANT"),
            ("N-04", "Normal Parking", "VACANT"),
            ("N-05", "Normal Parking", "VACANT"),
            ("N-06", "Normal Parking", "VACANT"),
            ("N-07", "Normal Parking", "VACANT"),
            ("N-08", "Normal Parking", "VACANT"),
            ("N-09", "Normal Parking", "VACANT"),
        ]
        cursor.executemany(
            "INSERT INTO parking_slots (slot_number, category, status) VALUES (?, ?, ?);",
            initial_slots
        )

    # Initial Seed Data: Default Pricing Policies
    cursor.execute("SELECT COUNT(*) FROM pricing_rules;")
    if cursor.fetchone()[0] == 0:
        default_pricing = [
            ("Disabled Parking", 60, 10, 30.0, 120, "CEIL_INTERVAL", "initial_setup"),
            ("EV Charging Parking", 60, 10, 60.0, 120, "CEIL_INTERVAL", "initial_setup"),
            ("Normal Parking", 60, 10, 50.0, 120, "CEIL_INTERVAL", "initial_setup"),
        ]
        cursor.executemany(
            """INSERT INTO pricing_rules 
               (category, free_minutes, grace_minutes, charge_amount, billing_interval_minutes, rounding_policy, updated_by) 
               VALUES (?, ?, ?, ?, ?, ?, ?);""",
            default_pricing
        )

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("SmartPark AI Database initialized successfully.")

