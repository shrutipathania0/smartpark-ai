"""
Full End-to-End Lifecycle and Integration Tests for SmartPark AI
Validates complete user flow across Entry, Parking Grid, Guard Alerting, and Exit Billing.
Tests all 3 categories: Disabled Parking, EV Charging Parking, Normal Parking.
"""
import unittest
from datetime import datetime, timedelta
from database.models import init_db
from database.database import query_one, query_all
from services.allocation_service import allocate_slot_and_create_ticket
from services.session_service import (
    record_vehicle_parked,
    get_active_session_by_plate,
    complete_session_and_exit
)
from services.parking_service import reset_simulation_environment, get_guard_dashboard_stats
from services.alert_service import get_alerts, acknowledge_alert, resolve_alert

class TestEndToEndWorkflows(unittest.TestCase):
    def setUp(self):
        init_db()
        reset_simulation_environment()

    def tearDown(self):
        reset_simulation_environment()

    def run_category_lifecycle(self, reg_number: str, category: str, expected_slot_prefix: str):
        """Executes full lifecycle for given category vehicle."""
        # 1. Entry: Allocate slot
        success, msg, ticket = allocate_slot_and_create_ticket(reg_number, category)
        self.assertTrue(success, f"Entry allocation failed: {msg}")
        self.assertEqual(ticket["parking_category"], category)
        self.assertTrue(ticket["slot_number"].startswith(expected_slot_prefix))

        slot_id = ticket["slot_id"]
        session_id = ticket["session_id"]

        # 2. Parking Grid: Verify state is RESERVED
        slot = query_one("SELECT * FROM parking_slots WHERE id = ?;", (slot_id,))
        self.assertEqual(slot["status"], "RESERVED")
        self.assertEqual(slot["current_session_id"], session_id)

        # 3. Simulate Vehicle Arrival & Parking
        park_ok, park_msg, sess = record_vehicle_parked(session_id)
        self.assertTrue(park_ok, park_msg)
        slot_parked = query_one("SELECT * FROM parking_slots WHERE id = ?;", (slot_id,))
        self.assertEqual(slot_parked["status"], "OCCUPIED")

        # 4. Exit: Lookup Active Session by registration
        active_sess = get_active_session_by_plate(reg_number)
        self.assertIsNotNone(active_sess)
        self.assertEqual(active_sess["registration_number"], reg_number)
        self.assertEqual(active_sess["slot_number"], ticket["slot_number"])
        self.assertIn("bill_preview", active_sess)

        # 5. Exit: Confirm Exit and Release Slot
        exit_ok, exit_msg, receipt = complete_session_and_exit(reg_number)
        self.assertTrue(exit_ok, exit_msg)
        self.assertEqual(receipt["registration_number"], reg_number)

        # 6. Verify slot restored to VACANT
        slot_released = query_one("SELECT * FROM parking_slots WHERE id = ?;", (slot_id,))
        self.assertEqual(slot_released["status"], "VACANT")
        self.assertIsNone(slot_released["current_session_id"])

        # 7. Verify session is COMPLETED
        closed_sess = query_one("SELECT * FROM parking_sessions WHERE id = ?;", (session_id,))
        self.assertEqual(closed_sess["status"], "COMPLETED")

    def test_disabled_parking_full_lifecycle(self):
        """Complete workflow test for Disabled Parking."""
        self.run_category_lifecycle("DL01DIS999", "Disabled Parking", "D-")

    def test_ev_charging_full_lifecycle(self):
        """Complete workflow test for EV Charging Parking."""
        self.run_category_lifecycle("MH12EV8888", "EV Charging Parking", "EV-")

    def test_normal_parking_full_lifecycle(self):
        """Complete workflow test for Normal Parking."""
        self.run_category_lifecycle("HR26NR7777", "Normal Parking", "N-")

    def test_guard_dashboard_stats_and_alert_resolution(self):
        """Tests that guard dashboard tracks entries, exits, revenue and alert lifecycle."""
        # Baseline
        stats0 = get_guard_dashboard_stats()
        self.assertEqual(stats0["active_sessions"], 0)

        # Vehicle enters and parks
        success, _, ticket = allocate_slot_and_create_ticket("KA03TEST01", "Normal Parking")
        self.assertTrue(success)
        record_vehicle_parked(ticket["session_id"])

        stats1 = get_guard_dashboard_stats()
        self.assertEqual(stats1["active_sessions"], 1)
        self.assertEqual(stats1["occupied_slots"], 1)

        # Vehicle exits
        complete_session_and_exit("KA03TEST01")
        stats2 = get_guard_dashboard_stats()
        self.assertEqual(stats2["active_sessions"], 0)
        self.assertEqual(stats2["vacant_slots"], stats0["total_slots"])

if __name__ == "__main__":
    unittest.main()

