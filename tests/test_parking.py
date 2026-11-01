"""
Unit Tests for Parking State Machine & Simulation Engine
"""
import unittest
from database.models import init_db
from database.database import query_one, query_all
from services.allocation_service import allocate_slot_and_create_ticket
from services.session_service import record_vehicle_parked
from services.parking_service import (
    simulate_place_object,
    simulate_clear_object,
    simulate_block_lane,
    simulate_park_incorrectly,
    reset_simulation_environment
)

class TestParkingSimulation(unittest.TestCase):
    def setUp(self):
        init_db()
        reset_simulation_environment()

    def tearDown(self):
        reset_simulation_environment()

    def test_correct_parking_flow(self):
        """Ticket creation reserves slot -> Vehicle parked changes RESERVED to OCCUPIED."""
        success, _, ticket = allocate_slot_and_create_ticket("DL01PK1000", "Normal Parking")
        self.assertTrue(success)

        slot = query_one("SELECT * FROM parking_slots WHERE id = ?;", (ticket["slot_id"],))
        self.assertEqual(slot["status"], "RESERVED")

        # Vehicle parks
        p_ok, msg, session = record_vehicle_parked(ticket["session_id"])
        self.assertTrue(p_ok, msg)

        slot_after = query_one("SELECT * FROM parking_slots WHERE id = ?;", (ticket["slot_id"],))
        self.assertEqual(slot_after["status"], "OCCUPIED")
        self.assertIsNotNone(session["parked_start_time"])

    def test_place_and_clear_object_preserves_state(self):
        """Placing object sets BLOCKED and alert; clearing restores previous status."""
        slot = query_one("SELECT id, status FROM parking_slots WHERE slot_number = 'N-01';")
        self.assertEqual(slot["status"], "VACANT")

        # Place object
        ok, msg = simulate_place_object(slot["id"])
        self.assertTrue(ok)
        slot_blocked = query_one("SELECT * FROM parking_slots WHERE id = ?;", (slot["id"],))
        self.assertEqual(slot_blocked["status"], "BLOCKED")
        self.assertEqual(slot_blocked["previous_status"], "VACANT")

        # Verify alert created
        alert = query_one("SELECT * FROM alerts WHERE slot_id = ? AND alert_type = 'OBJECT_OBSTRUCTION';", (slot["id"],))
        self.assertIsNotNone(alert)
        self.assertEqual(alert["status"], "OPEN")

        # Clear object
        c_ok, c_msg = simulate_clear_object(slot["id"])
        self.assertTrue(c_ok)
        slot_cleared = query_one("SELECT * FROM parking_slots WHERE id = ?;", (slot["id"],))
        self.assertEqual(slot_cleared["status"], "VACANT")

    def test_lane_blockage_alert_creation(self):
        """Lane blockage creates critical alert without altering slot assignments."""
        ok, msg = simulate_block_lane("Entry Lane 1")
        self.assertTrue(ok)
        alert = query_one("SELECT * FROM alerts WHERE alert_type = 'LANE_BLOCKAGE' ORDER BY id DESC LIMIT 1;")
        self.assertIsNotNone(alert)
        self.assertEqual(alert["severity"], "CRITICAL")
        self.assertIn("Entry Lane 1", alert["lane_id"])

if __name__ == "__main__":
    unittest.main()

