import random
import time
import datetime
from typing import Dict, Any, List
from database import db_manager

class ParkingSimulation:
    """
    Deterministic Streamlit-friendly parking lot and traffic simulator.
    Tracks vehicle arrival queues, random arrivals/departures, slot state transitions,
    entry/exit counters, and revenue generation.
    """
    
    def __init__(self):
        self.reset()
        
    def reset(self):
        """Resets simulation counters and synchronizes slots with Database state."""
        self.entry_count = 0
        self.exit_count = 0
        self.queue_length = 0
        self.total_wait_time_sec = 0
        self.total_processed_vehicles = 0
        self.sim_revenue = 0.0
        self.event_log = []
        self.is_running = False
        
        # Load slots from database
        db_slots = db_manager.get_all_slots()
        self.slots = {s["slot_id"]: s for s in db_slots}
        
    def get_summary(self) -> Dict[str, Any]:
        """Calculates current simulation metrics."""
        total = len(self.slots)
        available = len([s for s in self.slots.values() if s["status"] == "available"])
        occupied = len([s for s in self.slots.values() if s["status"] == "occupied"])
        reserved = len([s for s in self.slots.values() if s["status"] == "reserved"])
        unavailable = len([s for s in self.slots.values() if s["status"] == "unavailable"])
        
        avg_wait = (self.total_wait_time_sec / self.total_processed_vehicles) if self.total_processed_vehicles > 0 else 0.0
        occ_pct = round((occupied / total) * 100.0, 1) if total > 0 else 0.0
        
        return {
            "total_slots": total,
            "available_count": available,
            "occupied_count": occupied,
            "reserved_count": reserved,
            "unavailable_count": unavailable,
            "occupancy_pct": occ_pct,
            "entry_count": self.entry_count,
            "exit_count": self.exit_count,
            "queue_length": self.queue_length,
            "avg_wait_sec": round(avg_wait, 1),
            "sim_revenue": round(self.sim_revenue, 2),
            "is_running": self.is_running
        }

    def simulate_arrival(self, count: int = 1) -> List[str]:
        """Simulates vehicle arrival(s). Occupies available slots or adds to entry queue."""
        events = []
        for _ in range(count):
            available_slots = [s_id for s_id, s in self.slots.items() if s["status"] == "available"]
            if available_slots:
                # Pick a slot (favoring closer slots or random available)
                chosen_id = random.choice(available_slots)
                self.slots[chosen_id]["status"] = "occupied"
                db_manager.update_slot_status(chosen_id, "occupied")
                
                self.entry_count += 1
                self.total_processed_vehicles += 1
                
                # Calculate simulated parking fee revenue
                price = self.slots[chosen_id]["hourly_price"]
                fee = round(price * random.choice([0.5, 1.0, 1.5, 2.0]), 2)
                self.sim_revenue += fee
                
                msg = f"Vehicle arrived & parked in Slot `{chosen_id}` (+₹{fee:.2f})"
                events.append(msg)
                db_manager.log_event("sim_arrival", chosen_id, msg)
            else:
                self.queue_length += 1
                msg = f"Parking lot full! Vehicle added to entrance queue (Queue size: {self.queue_length})"
                events.append(msg)
                db_manager.log_event("sim_queue", None, msg)
                
        self._record_snapshot()
        return events

    def simulate_departure(self, count: int = 1) -> List[str]:
        """Simulates vehicle departure(s). Frees occupied slots and processes waiting queue if any."""
        events = []
        for _ in range(count):
            occupied_slots = [s_id for s_id, s in self.slots.items() if s["status"] == "occupied"]
            if occupied_slots:
                chosen_id = random.choice(occupied_slots)
                self.slots[chosen_id]["status"] = "available"
                db_manager.update_slot_status(chosen_id, "available")
                
                self.exit_count += 1
                msg = f"Vehicle departed from Slot `{chosen_id}`"
                events.append(msg)
                db_manager.log_event("sim_departure", chosen_id, msg)
                
                # If vehicles waiting in queue, park the first queued vehicle
                if self.queue_length > 0:
                    self.queue_length -= 1
                    self.slots[chosen_id]["status"] = "occupied"
                    db_manager.update_slot_status(chosen_id, "occupied")
                    
                    wait_time = random.randint(15, 120)
                    self.total_wait_time_sec += wait_time
                    self.total_processed_vehicles += 1
                    self.entry_count += 1
                    
                    q_msg = f"Queued vehicle entered into freed Slot `{chosen_id}` after {wait_time}s wait"
                    events.append(q_msg)
                    db_manager.log_event("sim_queue_entry", chosen_id, q_msg)
            else:
                msg = "No occupied slots to depart."
                events.append(msg)
                break
                
        self._record_snapshot()
        return events

    def toggle_slot(self, slot_id: str, new_status: str) -> None:
        """Manually sets slot status."""
        if slot_id in self.slots:
            self.slots[slot_id]["status"] = new_status
            db_manager.update_slot_status(slot_id, new_status)
            self._record_snapshot()

    def _record_snapshot(self):
        """Saves current state snapshot to database analytics."""
        s = self.get_summary()
        db_manager.save_analytics_snapshot(
            occupied=s["occupied_count"],
            available=s["available_count"],
            reserved=s["reserved_count"],
            total=s["total_slots"],
            revenue=s["sim_revenue"]
        )
