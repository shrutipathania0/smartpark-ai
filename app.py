"""
SmartPark AI - Main Application Server
Shared backend serving 4 interfaces:
1. Driver Entry Machine (/entry)
2. Parking Area Monitoring (/parking)
3. Guard Dashboard (/guard)
4. Driver Exit Machine (/exit)
"""
import os
import json
from datetime import datetime
from functools import wraps
from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash

from database.models import init_db
from database.database import query_all, query_one, execute_action
from services.allocation_service import (
    allocate_slot_and_create_ticket,
    get_slot_availability,
    check_active_session
)
from services.session_service import (
    get_active_session_by_plate,
    record_vehicle_parked,
    complete_session_and_exit
)
from services.pricing_service import (
    get_pricing_rules,
    update_pricing_rule,
    get_rule_for_category
)
from services.alert_service import (
    get_alerts,
    acknowledge_alert,
    resolve_alert
)
from services.parking_service import (
    get_all_slots,
    get_slot_detail,
    simulate_park_correctly,
    simulate_place_object,
    simulate_clear_object,
    simulate_park_incorrectly,
    simulate_block_lane,
    simulate_cross_parking,
    simulate_occupy_two_spaces,
    simulate_wrong_space,
    reset_simulation_environment,
    get_guard_dashboard_stats
)
from anpr.recognition_pipeline import (
    run_anpr_pipeline,
    decode_base64_image
)
from anpr.camera import capture_single_frame, get_fallback_demo_frame

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SMARTPARK_SECRET_KEY", "smartpark-ai-production-secret-key-2026")
app.config["JSON_SORT_KEYS"] = False
CORS(app)

# Initialize Database Schema
init_db()

# Guard Authentication Helpers
def init_guard_account():
    """Ensures at least one initial guard account exists with hashed password."""
    admin_guard = query_one("SELECT * FROM guards WHERE username = 'guard_admin';")
    if not admin_guard:
        default_hash = generate_password_hash("GuardPass@2026")
        execute_action(
            "INSERT INTO guards (username, password_hash) VALUES (?, ?);",
            ("guard_admin", default_hash)
        )
        print("[Auth] Initialized guard account: 'guard_admin'")

init_guard_account()

def guard_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "guard_user" not in session:
            if request.is_json:
                return jsonify({"error": "Unauthorized. Guard authentication required."}), 401
            return redirect(url_for("guard_login_page"))
        return f(*args, **kwargs)
    return decorated_function

# ==============================================================================
# FRONTEND TEMPLATE ROUTES
# ==============================================================================

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/entry")
def entry_machine():
    return render_template("entry.html")

@app.route("/parking")
def parking_monitoring():
    return render_template("parking.html")

@app.route("/guard/login", methods=["GET"])
def guard_login_page():
    if "guard_user" in session:
        return redirect(url_for("guard_dashboard"))
    return render_template("guard_login.html")

@app.route("/guard")
@guard_required
def guard_dashboard():
    return render_template("guard.html", guard_user=session["guard_user"])

@app.route("/exit")
def exit_machine():
    return render_template("exit.html")

# ==============================================================================
# REST API: ENTRY GATE
# ==============================================================================

@app.route("/api/entry/recognize", methods=["POST"])
def entry_recognize():
    """ANPR recognition endpoint for entry gate."""
    data = request.get_json(silent=True) or {}
    frame_b64 = data.get("frame")

    if frame_b64:
        image = decode_base64_image(frame_b64)
    else:
        # Local camera capture or fallback frame
        success, image, _ = capture_single_frame(camera_index=0)
        if not success or image is None:
            image = get_fallback_demo_frame()

    if image is None:
        return jsonify({"success": False, "error": "Unable to obtain image frame."}), 400

    result = run_anpr_pipeline(image, gate_type="ENTRY", save_capture=True)
    return jsonify(result)

@app.route("/api/entry/availability", methods=["GET"])
def entry_availability():
    """Returns slot availability counts per category."""
    counts = get_slot_availability()
    return jsonify({"success": True, "availability": counts})

@app.route("/api/entry/create-session", methods=["POST"])
def entry_create_session():
    """Allocates a compatible slot, changes state to RESERVED, and creates ticket."""
    data = request.get_json(silent=True) or {}
    reg = data.get("registration_number", "").strip().upper()
    cat = data.get("parking_category", "").strip()

    success, msg, ticket_data = allocate_slot_and_create_ticket(reg, cat)
    if not success:
        return jsonify({"success": False, "message": msg}), 400

    return jsonify({
        "success": True,
        "message": msg,
        "ticket": ticket_data
    })

# ==============================================================================
# REST API: PARKING MONITORING & SIMULATION
# ==============================================================================

@app.route("/api/parking/slots", methods=["GET"])
def parking_slots():
    """Returns all parking slots with session and alert information."""
    slots = get_all_slots()
    return jsonify({"success": True, "slots": slots})

@app.route("/api/parking/slots/<int:slot_id>", methods=["GET"])
def parking_slot_detail(slot_id):
    """Returns detail for single slot."""
    slot = get_slot_detail(slot_id)
    if not slot:
        return jsonify({"success": False, "message": "Slot not found"}), 404
    return jsonify({"success": True, "slot": slot})

@app.route("/api/parking/simulate", methods=["POST"])
def parking_simulate():
    """Executes a functional simulation scenario."""
    data = request.get_json(silent=True) or {}
    action = data.get("action", "").strip().lower()
    slot_id = data.get("slot_id")

    if action == "park_correctly":
        if not slot_id:
            return jsonify({"success": False, "message": "slot_id required"}), 400
        success, msg = simulate_park_correctly(int(slot_id))
    elif action == "place_object":
        if not slot_id:
            return jsonify({"success": False, "message": "slot_id required"}), 400
        success, msg = simulate_place_object(int(slot_id))
    elif action == "clear_object":
        if not slot_id:
            return jsonify({"success": False, "message": "slot_id required"}), 400
        success, msg = simulate_clear_object(int(slot_id))
    elif action == "park_incorrectly":
        reg = data.get("registration_number", "DL01AB9999")
        success, msg = simulate_park_incorrectly(int(slot_id) if slot_id else 1, reg)
    elif action == "block_lane":
        lane = data.get("lane_id", "Lane A - Entry")
        success, msg = simulate_block_lane(lane)
    elif action == "cross_parking":
        reg = data.get("registration_number", "MH12DE1234")
        success, msg = simulate_cross_parking(int(slot_id) if slot_id else 1, reg)
    elif action == "occupy_two_spaces":
        s1 = data.get("slot_id_1", 1)
        s2 = data.get("slot_id_2", 2)
        reg = data.get("registration_number", "KA03AB5678")
        success, msg = simulate_occupy_two_spaces(int(s1), int(s2), reg)
    elif action == "wrong_space":
        assigned_id = data.get("assigned_slot_id", 1)
        occupied_id = data.get("occupied_slot_id", 2)
        reg = data.get("registration_number", "UP16CD4321")
        success, msg = simulate_wrong_space(int(assigned_id), int(occupied_id), reg)
    elif action == "reset_simulation":
        success, msg = reset_simulation_environment()
    else:
        return jsonify({"success": False, "message": f"Unknown simulation action: {action}"}), 400

    return jsonify({"success": success, "message": msg})

@app.route("/api/parking/reset", methods=["POST"])
def parking_reset():
    """Resets parking environment safely."""
    success, msg = reset_simulation_environment()
    return jsonify({"success": success, "message": msg})

# ==============================================================================
# REST API: EXIT GATE
# ==============================================================================

@app.route("/api/exit/recognize", methods=["POST"])
def exit_recognize():
    """ANPR recognition endpoint for exit gate."""
    data = request.get_json(silent=True) or {}
    frame_b64 = data.get("frame")

    if frame_b64:
        image = decode_base64_image(frame_b64)
    else:
        success, image, _ = capture_single_frame(camera_index=0)
        if not success or image is None:
            image = get_fallback_demo_frame()

    if image is None:
        return jsonify({"success": False, "error": "Unable to obtain image frame."}), 400

    result = run_anpr_pipeline(image, gate_type="EXIT", save_capture=True)
    return jsonify(result)

@app.route("/api/exit/session/<registration_number>", methods=["GET"])
def exit_get_session(registration_number):
    """Retrieves active session and computed bill breakdown for confirmed plate."""
    session_data = get_active_session_by_plate(registration_number)
    if not session_data:
        return jsonify({
            "success": False,
            "message": f"No active parking session found for vehicle registration '{registration_number}'."
        }), 404

    return jsonify({
        "success": True,
        "session": session_data
    })

@app.route("/api/exit/confirm", methods=["POST"])
def exit_confirm():
    """Completes vehicle exit, finalizes bill, releases assigned slot."""
    data = request.get_json(silent=True) or {}
    reg = data.get("registration_number", "").strip().upper()

    success, msg, result_data = complete_session_and_exit(reg)
    if not success:
        return jsonify({"success": False, "message": msg}), 400

    return jsonify({
        "success": True,
        "message": msg,
        "exit_receipt": result_data
    })

# ==============================================================================
# REST API: GUARD DASHBOARD, AUTH, ALERTS & PRICING
# ==============================================================================

@app.route("/api/guard/login", methods=["POST"])
def guard_login_api():
    """Guard authentication endpoint."""
    data = request.get_json(silent=True) or {}
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()

    guard = query_one("SELECT * FROM guards WHERE username = ?;", (username,))
    if not guard or not check_password_hash(guard["password_hash"], password):
        return jsonify({"success": False, "message": "Invalid username or password."}), 401

    session["guard_user"] = username
    return jsonify({"success": True, "message": "Login successful.", "user": username})

@app.route("/api/guard/logout", methods=["POST"])
def guard_logout_api():
    """Guard logout endpoint."""
    session.pop("guard_user", None)
    return jsonify({"success": True, "message": "Logged out successfully."})

@app.route("/api/guard/dashboard", methods=["GET"])
@guard_required
def guard_dashboard_api():
    """Calculates all live dashboard statistics."""
    stats = get_guard_dashboard_stats()
    return jsonify({"success": True, "stats": stats})

@app.route("/api/guard/alerts", methods=["GET"])
@guard_required
def guard_alerts_api():
    """Lists alerts with optional status filter."""
    status = request.args.get("status")
    alerts = get_alerts(status_filter=status, limit=50)
    return jsonify({"success": True, "alerts": alerts})

@app.route("/api/guard/alerts/<int:alert_id>/acknowledge", methods=["POST"])
@guard_required
def guard_acknowledge_alert(alert_id):
    """Marks alert as acknowledged."""
    acknowledge_alert(alert_id)
    return jsonify({"success": True, "message": f"Alert #{alert_id} acknowledged."})

@app.route("/api/guard/alerts/<int:alert_id>/resolve", methods=["POST"])
@guard_required
def guard_resolve_alert(alert_id):
    """Marks alert as resolved."""
    resolve_alert(alert_id)
    return jsonify({"success": True, "message": f"Alert #{alert_id} resolved."})

@app.route("/api/guard/pricing", methods=["GET"])
@guard_required
def guard_get_pricing():
    """Retrieves current pricing rules for all categories."""
    rules = get_pricing_rules()
    return jsonify({"success": True, "pricing_rules": rules})

@app.route("/api/guard/pricing", methods=["PUT"])
@guard_required
def guard_update_pricing():
    """Updates category pricing rule. Preserves active session pricing snapshots."""
    data = request.get_json(silent=True) or {}
    cat = data.get("category")
    free_mins = int(data.get("free_minutes", 60))
    grace_mins = int(data.get("grace_minutes", 10))
    charge_amt = float(data.get("charge_amount", 50.0))
    interval_mins = int(data.get("billing_interval_minutes", 120))
    rounding = data.get("rounding_policy", "CEIL_INTERVAL")

    updated = update_pricing_rule(
        category=cat,
        free_minutes=free_mins,
        grace_minutes=grace_mins,
        charge_amount=charge_amt,
        billing_interval_minutes=interval_mins,
        rounding_policy=rounding,
        guard_username=session.get("guard_user", "guard")
    )
    return jsonify({"success": True, "message": f"Pricing updated for {cat}.", "rule": updated})

@app.route("/api/guard/history", methods=["GET"])
@guard_required
def guard_history():
    """Returns recent parking sessions and recognition logs for guard audit."""
    sessions = query_all(
        """SELECT s.*, p.slot_number 
           FROM parking_sessions s 
           JOIN parking_slots p ON s.slot_id = p.id 
           ORDER BY s.id DESC LIMIT 20;"""
    )
    logs = query_all("SELECT * FROM recognition_logs ORDER BY id DESC LIMIT 20;")
    return jsonify({"success": True, "recent_sessions": sessions, "recognition_logs": logs})

if __name__ == "__main__":
    print("\n=======================================================")
    print(" SmartPark AI - Intelligent Local Parking System")
    print(" Local URL: http://127.0.0.1:8000")
    print(" Guard Account: guard_admin / GuardPass@2026")
    print("=======================================================\n")
    app.run(host="127.0.0.1", port=8000, debug=False)

