import pytest
from modules import nlp_processor

def test_nlp_intent_find_parking():
    q = "Find parking near the entrance for an SUV under ₹50 per hour"
    res = nlp_processor.parse_user_query(q)
    assert res["intent"] in ["find_parking", "recommend_parking"]
    assert res["vehicle_type"] == "SUV"
    assert res["preferred_location"] == "entrance"
    assert res["max_hourly_price"] == 50.0

def test_nlp_intent_check_ev():
    q = "Show available EV charging spaces"
    res = nlp_processor.parse_user_query(q)
    assert res["intent"] == "check_availability" or res["needs_ev"] is True
    assert res["needs_ev"] is True

def test_nlp_intent_reserve_slot():
    q = "Reserve slot A04 for 30 minutes"
    res = nlp_processor.parse_user_query(q)
    assert res["intent"] == "reserve_parking"
    assert res["slot_id"] == "A04"
    assert res["duration_mins"] == 30

def test_nlp_intent_cancel_reservation():
    q = "Cancel my reservation RES-12345"
    res = nlp_processor.parse_user_query(q)
    assert res["intent"] == "cancel_reservation"
    assert res["reservation_id"] == "RES-12345"

def test_nlp_fallback_missing_credentials():
    q = "What can you do?"
    res = nlp_processor.parse_user_query(q)
    assert res["intent"] == "help"
