-- Database Schema for SmartPark AI

CREATE TABLE IF NOT EXISTS slots (
    slot_id TEXT PRIMARY KEY,
    zone TEXT NOT NULL,
    type TEXT NOT NULL,
    hourly_price REAL NOT NULL,
    distance_m INTEGER NOT NULL,
    has_ev BOOLEAN NOT NULL DEFAULT 0,
    is_accessible BOOLEAN NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'available',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS reservations (
    reservation_id TEXT PRIMARY KEY,
    slot_id TEXT NOT NULL,
    user_name TEXT DEFAULT 'Guest',
    vehicle_type TEXT DEFAULT 'Sedan',
    vehicle_number TEXT DEFAULT 'MH-01-AB-1234',
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP NOT NULL,
    duration_mins INTEGER NOT NULL,
    total_price REAL NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (slot_id) REFERENCES slots(slot_id)
);

CREATE TABLE IF NOT EXISTS parking_events (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    slot_id TEXT,
    event_type TEXT NOT NULL,
    details TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS analytics_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    occupied_count INTEGER NOT NULL,
    available_count INTEGER NOT NULL,
    reserved_count INTEGER NOT NULL,
    total_slots INTEGER NOT NULL,
    occupancy_pct REAL NOT NULL,
    revenue REAL NOT NULL DEFAULT 0.0,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
