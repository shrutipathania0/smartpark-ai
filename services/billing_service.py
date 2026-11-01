"""
Billing Engine for SmartPark AI
Calculates parking fees accurately using pricing snapshots and actual parked duration.
"""
import math
import json
from datetime import datetime
from typing import Dict, Any, Optional

def calculate_bill(
    pricing_snapshot_str: str,
    parked_start_time: Optional[datetime],
    exit_time: Optional[datetime],
    registration_number: str = "",
    category: str = "",
    slot_number: str = ""
) -> Dict[str, Any]:
    """
    Computes exact parking charges according to user-specified policies.
    - If vehicle was reserved but never parked (parked_start_time is None): fee is 0.
    - Initial policy: 60 mins free + 10 mins grace = 70 mins total free.
    - After 70 minutes: charge per started interval (e.g. 120 mins).
    """
    if isinstance(pricing_snapshot_str, str):
        try:
            rule = json.loads(pricing_snapshot_str)
        except Exception:
            rule = {
                "free_minutes": 60,
                "grace_minutes": 10,
                "charge_amount": 50.0,
                "billing_interval_minutes": 120,
                "rounding_policy": "CEIL_INTERVAL"
            }
    else:
        rule = pricing_snapshot_str or {}

    free_minutes = int(rule.get("free_minutes", 60))
    grace_minutes = int(rule.get("grace_minutes", 10))
    charge_amount = float(rule.get("charge_amount", 50.0))
    interval_minutes = int(rule.get("billing_interval_minutes", 120))
    rounding_policy = rule.get("rounding_policy", "CEIL_INTERVAL")

    # Unparked exit check
    if not parked_start_time or not exit_time:
        return {
            "registration_number": registration_number,
            "category": category,
            "slot_number": slot_number,
            "parked_start_time": None,
            "exit_time": exit_time.isoformat() if exit_time else None,
            "total_duration_minutes": 0,
            "total_duration_formatted": "0 mins",
            "free_minutes": free_minutes,
            "grace_minutes": grace_minutes,
            "chargeable_duration_minutes": 0,
            "billing_blocks": 0,
            "rate_per_block": charge_amount,
            "total_fee": 0.0,
            "is_unparked": True,
            "status_note": "Vehicle exited before parking. No charge applied."
        }

    # Calculate actual duration
    duration_seconds = max(0, int((exit_time - parked_start_time).total_seconds()))
    total_minutes = duration_seconds / 60.0

    combined_free_minutes = free_minutes + grace_minutes

    if total_minutes <= combined_free_minutes:
        chargeable_minutes = 0.0
        billing_blocks = 0
        total_fee = 0.0
    else:
        chargeable_minutes = total_minutes - combined_free_minutes
        if rounding_policy == "CEIL_INTERVAL":
            billing_blocks = math.ceil(chargeable_minutes / interval_minutes)
        else:
            billing_blocks = int(math.ceil(chargeable_minutes / interval_minutes))
        total_fee = round(billing_blocks * charge_amount, 2)

    # Format duration string
    hours = int(total_minutes // 60)
    mins = int(total_minutes % 60)
    secs = int(duration_seconds % 60)
    formatted_duration = f"{hours}h {mins}m {secs}s" if hours > 0 else f"{mins}m {secs}s"

    return {
        "registration_number": registration_number,
        "category": category,
        "slot_number": slot_number,
        "parked_start_time": parked_start_time.isoformat(),
        "exit_time": exit_time.isoformat(),
        "duration_seconds": duration_seconds,
        "total_duration_minutes": round(total_minutes, 1),
        "total_duration_formatted": formatted_duration,
        "free_minutes": free_minutes,
        "grace_minutes": grace_minutes,
        "combined_free_minutes": combined_free_minutes,
        "chargeable_duration_minutes": round(chargeable_minutes, 1),
        "billing_blocks": billing_blocks,
        "interval_minutes": interval_minutes,
        "rate_per_block": charge_amount,
        "total_fee": total_fee,
        "is_unparked": False,
        "status_note": "Fee calculated successfully."
    }

