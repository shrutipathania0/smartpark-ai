"""
Database Integrity and Schema Unit Tests for SmartPark AI
"""
import unittest
import sqlite3
import os
from database.models import init_db, get_db_connection
from database.database import query_all, query_one, execute_action

class TestDatabase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()

    def test_database_initialization(self):
        """Verifies database initializes and tables exist."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row["name"] for row in cursor.fetchall()]
        conn.close()

        expected = [
            "parking_slots", "parking_sessions", "pricing_rules",
            "guards", "alerts", "simulation_events", "recognition_logs", "parking_events"
        ]
        for t in expected:
            self.assertIn(t, tables, f"Expected table '{t}' not found in database.")

    def test_initial_slots_distribution(self):
        """Verifies initial 15 demonstration slots (3 Disabled, 3 EV, 9 Normal)."""
        slots = query_all("SELECT category, COUNT(*) as cnt FROM parking_slots GROUP BY category;")
        cat_map = {s["category"]: s["cnt"] for s in slots}

        self.assertEqual(cat_map.get("Disabled Parking"), 3)
        self.assertEqual(cat_map.get("EV Charging Parking"), 3)
        self.assertEqual(cat_map.get("Normal Parking"), 9)

    def test_pricing_rules_exist(self):
        """Verifies initial pricing rules exist for all 3 categories."""
        rules = query_all("SELECT category, free_minutes, grace_minutes, charge_amount FROM pricing_rules;")
        categories = {r["category"] for r in rules}
        self.assertIn("Disabled Parking", categories)
        self.assertIn("EV Charging Parking", categories)
        self.assertIn("Normal Parking", categories)

if __name__ == "__main__":
    unittest.main()

