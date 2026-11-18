import os
from functools import wraps
from datetime import datetime, date
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_from_directory
from werkzeug.security import check_password_hash, generate_password_hash

from config import Config
from database.models import db, ParkingSlot, ParkingSession, Guard, Alert, SimulationEvent, RecognitionLog, ParkingEvent
from database.database import init_db
from services.allocation_service import AllocationService
from services.session_service import SessionService
from services.parking_service import ParkingService
from services.pricing_service import PricingService
from services.billing_service import BillingService
from services.alert_service import AlertService
app = Flask(__name__)
app.config.from_object(Config)

# Initialize Database and seed defaults
init_db(app)

# ANPR — optional (heavy ML, may not be available on cloud)
try:
    from anpr.camera import CameraUtils
    from anpr.recognition_pipeline import ANPRPipeline
    anpr_pipeline = ANPRPipeline()
    ANPR_AVAILABLE = True
except Exception:
    CameraUtils = None
    ANPRPipeline = None
    anpr_pipeline = None
    ANPR_AVAILABLE = False

# --- Helper: Guard Authentication Decorator ---
def guard_login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('guard_id'):
            if request.path.startswith('/api/'):
                return jsonify({"success": False, "error": "Unauthorized. Guard login required."}), 401
            return redirect(url_for('guard_login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

# ==========================================
# PAGE ROUTES (FRONTEND INTERFACES)
# ==========================================

@app.route('/')
def home():
    """Portal Home: Overview of the 4 SmartPark AI Interfaces."""
    summary = AllocationService.get_availability_summary()
    return render_template('home.html', summary=summary)

@app.route('/entry')
def entry():
    """Interface 1: Driver Entry Machine."""
    summary = AllocationService.get_availability_summary()
    return render_template('entry.html', summary=summary, categories=Config.VALID_CATEGORIES)

@app.route('/parking')
def parking():
    """Interface 2: Parking Area Monitoring & Live Simulator."""
    slots = ParkingService.get_all_slots()
    return render_template('parking.html', slots=slots)

@app.route('/guard/login')
def guard_login():
    """Guard Authentication Page."""
    if session.get('guard_id'):
        return redirect(url_for('guard_dashboard'))
    return render_template('guard_login.html')

@app.route('/guard')
@guard_login_required
def guard_dashboard():
    """Interface 3: Guard Management & Security Dashboard."""
    return render_template('guard.html', guard_name=session.get('guard_name', 'Duty Guard'))

@app.route('/exit')
def exit_machine():
    """Interface 4: Driver Exit Machine."""
    return render_template('exit.html')

@app.route('/captures/<path:filename>')
def serve_capture(filename):
    """Serves stored capture images safely from data/captures."""
    return send_from_directory(Config.CAPTURES_DIR, filename)

# ==========================================
# API: ENTRY MACHINE (INTERFACE 1)
# ==========================================

@app.route('/api/entry/recognize', methods=['POST'])
def api_entry_recognize():
    """Receives webcam frame or image data and executes ANPR."""
    data = request.get_json(silent=True) or {}
    frame_data = data.get('frame')
    if not frame_data:
        return jsonify({"success": False, "error": "No frame image provided."}), 400

    if not ANPR_AVAILABLE or CameraUtils is None:
        return jsonify({"success": False, "error": "ANPR not available on this deployment."}), 503
    frame_bgr = CameraUtils.decode_base64_frame(frame_data)
    if frame_bgr is None:
        return jsonify({"success": False, "error": "Failed to decode camera frame."}), 400

    result = anpr_pipeline.process_frame(frame_bgr, gate_type="entry")
    return jsonify(result)

@app.route('/api/entry/availability', methods=['GET'])
def api_entry_availability():
    summary = AllocationService.get_availability_summary()
    return jsonify({"success": True, "availability": summary})

@app.route('/api/entry/create-session', methods=['POST'])
def api_entry_create_session():
    data = request.get_json(silent=True) or {}
    reg = data.get('registration_number', '').strip()
    category = data.get('parking_category', '').strip()

    if not reg or not category:
        return jsonify({"success": False, "error": "Registration number and category are required."}), 400

    result = AllocationService.allocate_slot(reg, category)
    status_code = 200 if result.get("success") else 400
    return jsonify(result), status_code

# ==========================================
# API: PARKING MONITORING (INTERFACE 2)
# ==========================================

@app.route('/api/parking/slots', methods=['GET'])
def api_parking_slots():
    slots = ParkingService.get_all_slots()
    summary = AllocationService.get_availability_summary()
    return jsonify({"success": True, "slots": slots, "summary": summary})

@app.route('/api/parking/slots/<int:slot_id>', methods=['GET'])
def api_parking_slot_detail(slot_id):
    slot = ParkingService.get_slot_by_id(slot_id)
    if not slot:
        return jsonify({"success": False, "error": "Slot not found"}), 404
    return jsonify({"success": True, "slot": slot})

@app.route('/api/parking/simulate', methods=['POST'])
def api_parking_simulate():
    data = request.get_json(silent=True) or {}
    action = data.get('action')

    if action == 'park_correctly':
        slot_id = data.get('slot_id')
        reg = data.get('registration_number')
        res = ParkingService.simulate_park_correctly(slot_id, reg)
    elif action == 'place_object':
        slot_id = data.get('slot_id')
        desc = data.get('description', 'Physical obstruction in parking space')
        if not slot_id:
            return jsonify({"success": False, "error": "slot_id required"}), 400
        res = ParkingService.simulate_place_object(slot_id, desc)
    elif action == 'clear_object':
        slot_id = data.get('slot_id')
        if not slot_id:
            return jsonify({"success": False, "error": "slot_id required"}), 400
        res = ParkingService.simulate_clear_object(slot_id)
    elif action == 'park_incorrectly':
        slot_id = data.get('slot_id', 1)
        reg = data.get('registration_number', 'DL01AB9999')
        res = ParkingService.simulate_park_incorrectly(slot_id, reg)
    elif action == 'block_lane':
        lane_id = data.get('lane_id', 'Main Entry Lane A')
        res = ParkingService.simulate_block_lane(lane_id)
    elif action == 'cross_parking':
        slot_id = data.get('slot_id', 1)
        reg = data.get('registration_number', 'MH12DE1234')
        res = ParkingService.simulate_cross_parking(slot_id, reg)
    elif action == 'occupy_two_spaces':
        s1 = data.get('slot1', 'N-04')
        s2 = data.get('slot2', 'N-05')
        reg = data.get('registration_number', 'KA05GH7890')
        res = ParkingService.simulate_occupy_two_spaces(s1, s2, reg)
    elif action == 'wrong_space':
        assigned = data.get('assigned_slot', 'N-01')
        occupied = data.get('occupied_slot', 'N-02')
        reg = data.get('registration_number', 'HR26DK8888')
        res = ParkingService.simulate_wrong_space(assigned, occupied, reg)
    else:
        return jsonify({"success": False, "error": f"Unknown simulation action '{action}'"}), 400

    status_code = 200 if res.get("success") else 400
    return jsonify(res), status_code

@app.route('/api/parking/reset', methods=['POST'])
def api_parking_reset():
    res = ParkingService.simulate_reset()
    return jsonify(res)

# ==========================================
# API: EXIT MACHINE (INTERFACE 4)
# ==========================================

@app.route('/api/exit/recognize', methods=['POST'])
def api_exit_recognize():
    """Receives webcam frame at exit gate, runs ANPR, and queries active session."""
    data = request.get_json(silent=True) or {}
    frame_data = data.get('frame')
    if not frame_data:
        return jsonify({"success": False, "error": "No frame image provided."}), 400

    if not ANPR_AVAILABLE or CameraUtils is None:
        return jsonify({"success": False, "error": "ANPR not available on this deployment."}), 503
    frame_bgr = CameraUtils.decode_base64_frame(frame_data)
    if frame_bgr is None:
        return jsonify({"success": False, "error": "Failed to decode camera frame."}), 400

    anpr_res = anpr_pipeline.process_frame(frame_bgr, gate_type="exit")

    # If plate was recognized with high/medium confidence, attempt active session lookup
    session_data = None
    bill_data = None
    reg = anpr_res.get("registration_number")
    if reg:
        sess = SessionService.get_active_session_by_registration(reg)
        if sess:
            session_data = sess.to_dict()
            bill_data = BillingService.calculate_bill(sess)

    anpr_res["session"] = session_data
    anpr_res["bill"] = bill_data
    return jsonify(anpr_res)

@app.route('/api/exit/session/<registration_number>', methods=['GET'])
def api_exit_session_lookup(registration_number):
    clean_reg = registration_number.strip().upper().replace(" ", "").replace("-", "")
    sess = SessionService.get_active_session_by_registration(clean_reg)
    if not sess:
        return jsonify({
            "success": False,
            "error": f"No active parking session found for vehicle registration {clean_reg}."
        }), 404

    bill_data = BillingService.calculate_bill(sess)
    return jsonify({
        "success": True,
        "session": sess.to_dict(),
        "bill": bill_data
    })

@app.route('/api/exit/confirm', methods=['POST'])
def api_exit_confirm():
    data = request.get_json(silent=True) or {}
    session_id = data.get('session_id')
    if not session_id:
        return jsonify({"success": False, "error": "session_id required."}), 400

    res = SessionService.process_exit(session_id)
    status_code = 200 if res.get("success") else 400
    return jsonify(res), status_code

@app.route('/api/exit/cancel-reservation', methods=['POST'])
def api_exit_cancel_reservation():
    data = request.get_json(silent=True) or {}
    session_id = data.get('session_id')
    reason = data.get('reason', 'Driver cancelled exit / did not park')
    if not session_id:
        return jsonify({"success": False, "error": "session_id required."}), 400

    res = SessionService.cancel_reservation(session_id, reason=reason)
    status_code = 200 if res.get("success") else 400
    return jsonify(res), status_code

# ==========================================
# API: GUARD DASHBOARD (INTERFACE 3)
# ==========================================

@app.route('/api/guard/login', methods=['POST'])
def api_guard_login():
    data = request.get_json(silent=True) or {}
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()

    if not username or not password:
        return jsonify({"success": False, "error": "Username and password required."}), 400

    guard = Guard.query.filter_by(username=username).first()
    if guard and check_password_hash(guard.password_hash, password):
        session['guard_id'] = guard.id
        session['guard_username'] = guard.username
        session['guard_name'] = guard.full_name
        return jsonify({
            "success": True,
            "message": "Login successful",
            "guard": guard.to_dict(),
            "redirect": "/guard"
        })

    return jsonify({"success": False, "error": "Invalid username or password."}), 401

@app.route('/api/guard/logout', methods=['POST', 'GET'])
def api_guard_logout():
    session.clear()
    if request.path.startswith('/api/'):
        return jsonify({"success": True, "message": "Logged out successfully"})
    return redirect(url_for('guard_login'))

@app.route('/api/guard/dashboard', methods=['GET'])
@guard_login_required
def api_guard_dashboard_stats():
    # Slot and category counts
    availability = AllocationService.get_availability_summary()

    # Sessions today
    today_start = datetime.combine(date.today(), datetime.min.time())
    entries_today = ParkingSession.query.filter(ParkingSession.entry_time >= today_start).count()
    exits_today = ParkingSession.query.filter(ParkingSession.exit_time >= today_start, ParkingSession.status == "COMPLETED").count()

    # Revenue today
    completed_today = ParkingSession.query.filter(ParkingSession.exit_time >= today_start, ParkingSession.status == "COMPLETED").all()
    revenue_today = sum(s.final_amount for s in completed_today)

    # Active sessions
    active_count = ParkingSession.query.filter(ParkingSession.status.in_(["ACTIVE_RESERVED", "ACTIVE_PARKED"])).count()

    # Open alerts
    open_alerts = Alert.query.filter(Alert.status.in_(["OPEN", "ACKNOWLEDGED"])).count()

    return jsonify({
        "success": True,
        "stats": {
            "total_slots": availability["total_slots"],
            "vacant_slots": availability["vacant"],
            "reserved_slots": availability["reserved"],
            "occupied_slots": availability["occupied"],
            "blocked_slots": availability["blocked"],
            "active_sessions": active_count,
            "entries_today": entries_today,
            "exits_today": exits_today,
            "revenue_today": round(revenue_today, 2),
            "open_alerts": open_alerts,
            "by_category": availability["by_category"]
        }
    })

@app.route('/api/guard/recent-activity', methods=['GET'])
@guard_login_required
def api_guard_recent_activity():
    recent_sessions = ParkingSession.query.order_by(ParkingSession.updated_at.desc()).limit(20).all()
    return jsonify({
        "success": True,
        "recent_sessions": [s.to_dict() for s in recent_sessions]
    })

@app.route('/api/guard/alerts', methods=['GET'])
@guard_login_required
def api_guard_alerts():
    alerts = AlertService.get_all_alerts(limit=50)
    return jsonify({"success": True, "alerts": alerts})

@app.route('/api/guard/alerts/<int:alert_id>/acknowledge', methods=['POST'])
@guard_login_required
def api_guard_alert_ack(alert_id):
    res = AlertService.acknowledge_alert(alert_id)
    return jsonify(res)

@app.route('/api/guard/alerts/<int:alert_id>/resolve', methods=['POST'])
@guard_login_required
def api_guard_alert_resolve(alert_id):
    res = AlertService.resolve_alert(alert_id)
    return jsonify(res)

@app.route('/api/guard/pricing', methods=['GET'])
@guard_login_required
def api_guard_get_pricing():
    rules = PricingService.get_all_pricing_rules()
    return jsonify({"success": True, "pricing_rules": rules})

@app.route('/api/guard/pricing', methods=['PUT'])
@guard_login_required
def api_guard_update_pricing():
    data = request.get_json(silent=True) or {}
    category = data.get('category')
    if category not in Config.VALID_CATEGORIES:
        return jsonify({"success": False, "error": f"Invalid category: {category}"}), 400

    free_min = data.get('free_minutes', 60)
    grace_min = data.get('grace_minutes', 10)
    amount = data.get('charge_amount', 50.0)
    interval = data.get('billing_interval_minutes', 120)
    policy = data.get('rounding_policy', 'CEIL')
    guard_user = session.get('guard_username', 'Guard')

    updated = PricingService.update_pricing_rule(
        category=category,
        free_minutes=free_min,
        grace_minutes=grace_min,
        charge_amount=amount,
        billing_interval_minutes=interval,
        rounding_policy=policy,
        updated_by=f"Guard ({guard_user})"
    )
    return jsonify({"success": True, "pricing_rule": updated})

if __name__ == '__main__':
    print(f"Starting SmartPark AI local server on http://{Config.HOST}:{Config.PORT}")
    app.run(host=Config.HOST, port=Config.PORT, debug=True)

