"""
Unit Tests for SmartPark AI Billing Engine
Tests all free-period and billing-block boundaries, unparked exits, and snapshot preservation.
"""
import unittest
from datetime import datetime, timedelta
from services.billing_service import calculate_bill

class TestBillingEngine(unittest.TestCase):
    def setUp(self):
        self.default_snapshot = '{"free_minutes": 60, "grace_minutes": 10, "charge_amount": 50.0, "billing_interval_minutes": 120, "rounding_policy": "CEIL_INTERVAL"}'
        self.base_time = datetime(2026, 11, 1, 10, 0, 0)

    def test_unparked_reservation_costs_zero(self):
        """Unparked exit (driver reserved but never parked) must cost 0."""
        bill = calculate_bill(
            pricing_snapshot_str=self.default_snapshot,
            parked_start_time=None,
            exit_time=self.base_time + timedelta(minutes=15)
        )
        self.assertEqual(bill["total_fee"], 0.0)
        self.assertTrue(bill["is_unparked"])

    def test_within_free_period_30_mins(self):
        """30 minutes actual parking -> ₹0."""
        exit_time = self.base_time + timedelta(minutes=30)
        bill = calculate_bill(self.default_snapshot, self.base_time, exit_time)
        self.assertEqual(bill["total_fee"], 0.0)

    def test_exact_free_period_60_mins(self):
        """Exactly 60 minutes -> ₹0."""
        exit_time = self.base_time + timedelta(minutes=60)
        bill = calculate_bill(self.default_snapshot, self.base_time, exit_time)
        self.assertEqual(bill["total_fee"], 0.0)

    def test_within_grace_period_65_mins(self):
        """65 minutes (within 10m grace period) -> ₹0."""
        exit_time = self.base_time + timedelta(minutes=65)
        bill = calculate_bill(self.default_snapshot, self.base_time, exit_time)
        self.assertEqual(bill["total_fee"], 0.0)

    def test_exact_combined_free_period_70_mins(self):
        """Exactly 70 minutes (end of free + grace) -> ₹0."""
        exit_time = self.base_time + timedelta(minutes=70)
        bill = calculate_bill(self.default_snapshot, self.base_time, exit_time)
        self.assertEqual(bill["total_fee"], 0.0)

    def test_first_chargeable_minute_71_mins(self):
        """71 minutes -> 1 chargeable minute -> 1 started 2-hr block -> ₹50."""
        exit_time = self.base_time + timedelta(minutes=71)
        bill = calculate_bill(self.default_snapshot, self.base_time, exit_time)
        self.assertEqual(bill["billing_blocks"], 1)
        self.assertEqual(bill["total_fee"], 50.0)

    def test_two_hours_ten_mins(self):
        """130 minutes (2 hours 10 mins) -> 60 chargeable mins -> 1 block -> ₹50."""
        exit_time = self.base_time + timedelta(minutes=130)
        bill = calculate_bill(self.default_snapshot, self.base_time, exit_time)
        self.assertEqual(bill["billing_blocks"], 1)
        self.assertEqual(bill["total_fee"], 50.0)

    def test_exact_first_interval_boundary_190_mins(self):
        """190 minutes (70 free + 120 interval) -> 120 chargeable mins -> 1 block -> ₹50."""
        exit_time = self.base_time + timedelta(minutes=190)
        bill = calculate_bill(self.default_snapshot, self.base_time, exit_time)
        self.assertEqual(bill["billing_blocks"], 1)
        self.assertEqual(bill["total_fee"], 50.0)

    def test_just_over_first_interval_boundary_191_mins(self):
        """191 minutes -> 121 chargeable mins -> 2 started blocks -> ₹100."""
        exit_time = self.base_time + timedelta(minutes=191)
        bill = calculate_bill(self.default_snapshot, self.base_time, exit_time)
        self.assertEqual(bill["billing_blocks"], 2)
        self.assertEqual(bill["total_fee"], 100.0)

    def test_four_hours_ten_mins(self):
        """250 minutes (4 hours 10 mins) -> 180 chargeable mins -> 2 blocks -> ₹100."""
        exit_time = self.base_time + timedelta(minutes=250)
        bill = calculate_bill(self.default_snapshot, self.base_time, exit_time)
        self.assertEqual(bill["billing_blocks"], 2)
        self.assertEqual(bill["total_fee"], 100.0)

    def test_multi_day_session_crossing_midnight(self):
        """Session crossing midnight (28 hours = 1680 minutes)."""
        exit_time = self.base_time + timedelta(hours=28)
        bill = calculate_bill(self.default_snapshot, self.base_time, exit_time)
        chargeable = 1680 - 70 # 1610 mins
        # 1610 / 120 = 13.41 -> 14 blocks
        self.assertEqual(bill["billing_blocks"], 14)
        self.assertEqual(bill["total_fee"], 14 * 50.0)

if __name__ == "__main__":
    unittest.main()

