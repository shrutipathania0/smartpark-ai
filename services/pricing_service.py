"""
Pricing Service for SmartPark AI
Handles category-specific pricing rules, configuration, and snapshots.
"""
import json
from datetime import datetime
from database.database import query_all, query_one, execute_action

def get_pricing_rules():
    """Retrieve current pricing rules for all 3 categories."""
    rules = query_all("SELECT * FROM pricing_rules ORDER BY category;")
    return {r["category"]: r for r in rules}

def get_rule_for_category(category: str):
    """Retrieve rule for specific category."""
    rule = query_one("SELECT * FROM pricing_rules WHERE category = ?;", (category,))
    if not rule:
        # Fallback default if not in db
        return {
            "category": category,
            "free_minutes": 60,
            "grace_minutes": 10,
            "charge_amount": 50.0,
            "billing_interval_minutes": 120,
            "rounding_policy": "CEIL_INTERVAL"
        }
    return rule

def update_pricing_rule(category: str, free_minutes: int, grace_minutes: int, 
                        charge_amount: float, billing_interval_minutes: int, 
                        rounding_policy: str, guard_username: str):
    """Update pricing rules (Guard only). Does not affect active sessions."""
    execute_action(
        """UPDATE pricing_rules 
           SET free_minutes = ?, grace_minutes = ?, charge_amount = ?, 
               billing_interval_minutes = ?, rounding_policy = ?, 
               updated_by = ?, updated_at = CURRENT_TIMESTAMP
           WHERE category = ?;""",
        (free_minutes, grace_minutes, charge_amount, billing_interval_minutes, rounding_policy, guard_username, category)
    )
    return get_rule_for_category(category)

def create_pricing_snapshot(category: str) -> str:
    """Create a JSON snapshot of the pricing rule to lock in for a session."""
    rule = get_rule_for_category(category)
    return json.dumps({
        "category": rule["category"],
        "free_minutes": rule["free_minutes"],
        "grace_minutes": rule["grace_minutes"],
        "charge_amount": rule["charge_amount"],
        "billing_interval_minutes": rule["billing_interval_minutes"],
        "rounding_policy": rule["rounding_policy"],
        "snapshot_timestamp": datetime.utcnow().isoformat()
    })

