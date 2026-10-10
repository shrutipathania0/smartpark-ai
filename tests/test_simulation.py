import pytest
from modules.simulation_engine import ParkingSimulation

def test_simulation_initial_state():
    sim = ParkingSimulation()
    summary = sim.get_summary()
    assert summary["total_slots"] == 24
    assert summary["entry_count"] == 0
    assert summary["exit_count"] == 0

def test_simulation_arrivals_and_departures():
    sim = ParkingSimulation()
    sim.simulate_arrival(3)
    s1 = sim.get_summary()
    assert s1["entry_count"] == 3
    assert s1["occupied_count"] >= 3 or s1["queue_length"] > 0

    sim.simulate_departure(2)
    s2 = sim.get_summary()
    assert s2["exit_count"] == 2

def test_simulation_manual_toggle():
    sim = ParkingSimulation()
    sim.toggle_slot("A01", "occupied")
    assert sim.slots["A01"]["status"] == "occupied"

    sim.toggle_slot("A01", "available")
    assert sim.slots["A01"]["status"] == "available"
