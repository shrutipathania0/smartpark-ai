import pytest
from modules import recommendation_engine

@pytest.fixture
def sample_slots():
    return [
        {"slot_id": "A01", "zone": "Zone A", "type": "SUV", "hourly_price": 60, "distance_m": 15, "has_ev": False, "is_accessible": False, "status": "available"},
        {"slot_id": "A02", "zone": "Zone A", "type": "SUV", "hourly_price": 60, "distance_m": 18, "has_ev": False, "is_accessible": False, "status": "occupied"},
        {"slot_id": "C01", "zone": "Zone C", "type": "EV", "hourly_price": 45, "distance_m": 25, "has_ev": True, "is_accessible": False, "status": "available"},
        {"slot_id": "C04", "zone": "Zone C", "type": "Accessible", "hourly_price": 30, "distance_m": 12, "has_ev": False, "is_accessible": True, "status": "available"},
        {"slot_id": "D01", "zone": "Zone D", "type": "Compact", "hourly_price": 25, "distance_m": 85, "has_ev": False, "is_accessible": False, "status": "available"},
    ]

def test_recommendation_filters_occupied(sample_slots):
    ranked = recommendation_engine.rank_parking_slots(sample_slots)
    slot_ids = [r["slot_id"] for r in ranked]
    assert "A02" not in slot_ids  # Occupied slot must be filtered out

def test_recommendation_ev_constraint(sample_slots):
    ranked = recommendation_engine.rank_parking_slots(sample_slots, needs_ev=True)
    assert len(ranked) == 1
    assert ranked[0]["slot_id"] == "C01"

def test_recommendation_price_constraint(sample_slots):
    ranked = recommendation_engine.rank_parking_slots(sample_slots, max_hourly_price=35.0)
    slot_ids = [r["slot_id"] for r in ranked]
    assert "A01" not in slot_ids
    assert "D01" in slot_ids or "C04" in slot_ids

def test_recommendation_ranking_proximity(sample_slots):
    ranked = recommendation_engine.rank_parking_slots(sample_slots, preferred_location="entrance")
    assert ranked[0]["slot_id"] == "C04" or ranked[0]["slot_id"] == "A01"
