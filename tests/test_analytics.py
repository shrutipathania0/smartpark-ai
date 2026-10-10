import pytest
from modules import analytics_engine

def test_analytics_empty_states():
    fig_pie = analytics_engine.create_occupancy_pie_chart([])
    assert fig_pie is not None

    fig_timeline = analytics_engine.create_occupancy_timeline_chart([])
    assert fig_timeline is not None

    fig_rev = analytics_engine.create_revenue_timeline_chart([])
    assert fig_rev is not None

def test_analytics_valid_slots():
    sample_slots = [
        {"slot_id": "A01", "zone": "Zone A", "status": "available"},
        {"slot_id": "A02", "zone": "Zone A", "status": "occupied"},
        {"slot_id": "B01", "zone": "Zone B", "status": "reserved"},
    ]
    fig = analytics_engine.create_occupancy_pie_chart(sample_slots)
    assert fig is not None
