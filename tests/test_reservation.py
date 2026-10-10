import pytest
import os
import tempfile
from database import db_manager

@pytest.fixture
def temp_db():
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(db_fd)
    db_manager.init_db(db_path)
    yield db_path
    if os.path.exists(db_path):
        os.remove(db_path)

def test_reservation_lifecycle(temp_db):
    # Make a reservation
    res = db_manager.create_reservation(
        slot_id="A01",
        user_name="Test User",
        vehicle_type="SUV",
        duration_mins=60,
        db_path=temp_db
    )
    assert res["success"] is True
    res_id = res["reservation"]["reservation_id"]

    # Slot state should be updated to reserved
    slot = db_manager.get_slot_by_id("A01", temp_db)
    assert slot["status"] == "reserved"

    # Cancel reservation
    cancel_res = db_manager.cancel_reservation(res_id, temp_db)
    assert cancel_res["success"] is True

    # Slot should be available again
    slot_after = db_manager.get_slot_by_id("A01", temp_db)
    assert slot_after["status"] == "available"

def test_double_booking_prevention(temp_db):
    # First reservation succeeds
    res1 = db_manager.create_reservation("A01", user_name="User 1", db_path=temp_db)
    assert res1["success"] is True

    # Second reservation on same slot fails
    res2 = db_manager.create_reservation("A01", user_name="User 2", db_path=temp_db)
    assert res2["success"] is False
    assert "cannot be reserved" in res2["message"] or "occupied" in res2["message"] or "reserved" in res2["message"]
