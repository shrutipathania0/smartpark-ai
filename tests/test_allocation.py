"""
Allocation and State Machine Tests for SmartPark AI
Verifies category compatibility, duplicate prevention, and atomic reservations.
"""
import unittest
from database.models import init_db
from database.database import query_one, execute_action
from services.allocation_service import allocate_slot_and_create_ticket
from services.parking_service import reset_simulation_environment

class TestAllocationService(unittest.TestCase):
    def setUp(self):
        init_db()
        reset_simulation_environment()

    def tearDown(self):
        reset_simulation_environment()

    def test_disabled_category_allocation(self):
        """Disabled vehicle must ONLY receive a Disabled Parking slot."""
        success, msg, ticket = allocate_slot_and_create_ticket("DL01DIS001", "Disabled Parking")
        self.assertTrue(success, msg)
        self.assertEqual(ticket["parking_category"], "Disabled Parking")
        self.assertTrue(ticket["slot_number"].startswith("D-"))

    def test_ev_category_allocation(self):
        """EV vehicle must ONLY receive an EV Charging Parking slot."""
        success, msg, ticket = allocate_slot_and_create_ticket("MH12EV0002", "EV Charging Parking")
        self.assertTrue(success, msg)
        self.assertEqual(ticket["parking_category"], "EV Charging Parking")
        self.assertTrue(ticket["slot_number"].startswith("EV-"))

    def test_normal_category_allocation(self):
        """Normal vehicle must ONLY receive a Normal Parking slot."""
        success, msg, ticket = allocate_slot_and_create_ticket("HR26NR0003", "Normal Parking")
        self.assertTrue(success, msg)
        self.assertEqual(ticket["parking_category"], "Normal Parking")
        self.assertTrue(ticket["slot_number"].startswith("N-"))

    def test_duplicate_active_session_prevention(self):
        """Same registration cannot create two active sessions simultaneously."""
        success1, _, _ = allocate_slot_and_create_ticket("KA03DUP111", "Normal Parking")
        self.assertTrue(success1)

        success2, msg2, ticket2 = allocate_slot_and_create_ticket("KA03DUP111", "Normal Parking")
        self.assertFalse(success2)
        self.assertIn("already has an active parking session", msg2)
        self.assertIsNone(ticket2)

    def test_no_allocation_when_category_exhausted(self):
        """When all 3 slots of a category are reserved, the 4th request must fail cleanly."""
        for i in range(1, 4):
            s, _, _ = allocate_slot_and_create_ticket(f"EVTEST0{i}", "EV Charging Parking")
            self.assertTrue(s)

        # 4th request must fail
        s_extra, msg_extra, _ = allocate_slot_and_create_ticket("EVTEST04", "EV Charging Parking")
        self.assertFalse(s_extra)
        self.assertIn("No available vacant slots", msg_extra)

if __name__ == "__main__":
    unittest.main()

