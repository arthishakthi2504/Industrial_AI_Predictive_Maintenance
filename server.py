
from flask import Flask, request, jsonify
import pandas as pd
import joblib
import os
import math
import logging
from datetime import datetime

# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

MODEL_FILE = os.path.join(
    BASE_DIR, "ml", "anomaly_model.pkl"
)

LIVE_DATA_FILE = os.path.join(
    BASE_DIR, "data", "live_data.csv"
)

FEATURES = [
    "temperature",
    "vibration",
    "current",
    "rpm"
]

# Demo thresholds only. Not universal safety limits.
TEMP_HIGH = 75.0
VIBRATION_HIGH = 0.80
CURRENT_HIGH = 5.00
RPM_LOW = 1200
RPM_HIGH = 1600

# ============================================================
# FLASK APPLICATION
# ============================================================

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)

# ============================================================
# LOAD AI MODEL
# ============================================================

print("==============================================")
print("       INDUSTRIAL AI MONITORING SERVER")
print("==============================================")

if not os.path.exists(MODEL_FILE):
    raise FileNotFoundError(
        f"AI model not found: {MODEL_FILE}\n"
        "Run: python ml/train_model.py"
    )

model = joblib.load(MODEL_FILE)

print("AI model loaded successfully.")
print("Model:", MODEL_FILE)

# ============================================================
# CREATE LIVE DATA FILE
# ============================================================

os.makedirs(os.path.dirname(LIVE_DATA_FILE), exist_ok=True)

CSV_COLUMNS = [
    "timestamp",
    "temperature",
    "vibration",
    "current",
    "rpm",
    "ml_status",
    "machine_health",
    "maintenance",
    "evidence"
]

if not os.path.exists(LIVE_DATA_FILE):
    pd.DataFrame(columns=CSV_COLUMNS).to_csv(
        LIVE_DATA_FILE,
        index=False
    )
    print("Live data file created.")

# ============================================================
# MACHINE CONDITION ANALYSIS
# ============================================================

def analyze_machine(temperature, vibration, current, rpm):

    input_data = pd.DataFrame([{
        "temperature": temperature,
        "vibration": vibration,
        "current": current,
        "rpm": rpm
    }], columns=FEATURES)

    prediction = model.predict(input_data)[0]

    ml_status = "ANOMALY" if prediction == -1 else "NORMAL"

    evidence = []

    if temperature >= TEMP_HIGH:
        evidence.append("High temperature")

    if vibration >= VIBRATION_HIGH:
        evidence.append("High vibration")

    if current >= CURRENT_HIGH:
        evidence.append("High current")

    if rpm <= RPM_LOW:
        evidence.append("Low RPM")

    if rpm >= RPM_HIGH:
        evidence.append("High RPM")

    if ml_status == "ANOMALY" and evidence:
        machine_health = "CRITICAL"
        maintenance = (
            "Maintenance required. "
            "Inspect machine immediately."
        )
    elif ml_status == "ANOMALY":
        machine_health = "WARNING"
        maintenance = (
            "AI detected abnormal machine behavior. "
            "Inspect machine condition."
        )
    elif evidence:
        machine_health = "WARNING"
        maintenance = "Sensor condition requires inspection."
    else:
        machine_health = "HEALTHY"
        maintenance = "Machine operating normally."

    evidence_text = (
        ", ".join(evidence)
        if evidence
        else "No abnormal sensor conditions detected."
    )

    return {
        "ml_status": ml_status,
        "machine_health": machine_health,
        "maintenance": maintenance,
        "evidence": evidence_text
    }

# ============================================================
# SENSOR API
# ============================================================

@app.route("/api/sensor", methods=["POST"])
def receive_sensor_data():

    # Check request content type
    if not request.is_json:
        return jsonify({
            "success": False,
            "error": "Content-Type must be application/json"
        }), 400

    # Parse JSON without raising a BadRequest exception
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "success": False,
            "error": "Invalid or missing JSON object"
        }), 400

    # Validate required fields
    missing_fields = [
        field for field in FEATURES
        if field not in data
    ]

    if missing_fields:
        return jsonify({
            "success": False,
            "error": "Missing sensor fields: "
                     + ", ".join(missing_fields)
        }), 400

    # Convert and validate numeric values
    try:
        temperature = float(data["temperature"])
        vibration = float(data["vibration"])
        current = float(data["current"])
        rpm = float(data["rpm"])
    except (TypeError, ValueError):
        return jsonify({
            "success": False,
            "error": "Sensor values must be numeric"
        }), 400

    values = [
        temperature,
        vibration,
        current,
        rpm
    ]

    if not all(math.isfinite(value) for value in values):
        return jsonify({
            "success": False,
            "error": "Sensor values must be finite numbers"
        }), 400

    try:
        # Analyze machine condition
        result = analyze_machine(
            temperature,
            vibration,
            current,
            rpm
        )

        timestamp = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        # Prepare CSV row
        row = {
            "timestamp": timestamp,
            "temperature": temperature,
            "vibration": vibration,
            "current": current,
            "rpm": rpm,
            "ml_status": result["ml_status"],
            "machine_health": result["machine_health"],
            "maintenance": result["maintenance"],
            "evidence": result["evidence"]
        }

        # Save sensor reading
        pd.DataFrame([row], columns=CSV_COLUMNS).to_csv(
            LIVE_DATA_FILE,
            mode="a",
            header=False,
            index=False
        )

        # Display reading in terminal
        print()
        print("==============================================")
        print("           NEW SENSOR READING")
        print("==============================================")
        print(f"Temperature : {temperature:.2f} °C")
        print(f"Vibration   : {vibration:.2f}")
        print(f"Current     : {current:.2f} A")
        print(f"RPM         : {rpm:.0f}")
        print("----------------------------------------------")
        print(f"AI Status   : {result['ml_status']}")
        print(f"Health      : {result['machine_health']}")
        print(f"Evidence    : {result['evidence']}")
        print(f"Action      : {result['maintenance']}")
        print("==============================================")

        # Send response to client
        return jsonify({
            "success": True,
            "timestamp": timestamp,
            "temperature": temperature,
            "vibration": vibration,
            "current": current,
            "rpm": rpm,
            "ml_status": result["ml_status"],
            "machine_health": result["machine_health"],
            "maintenance": result["maintenance"],
            "evidence": result["evidence"]
        }), 200

    except Exception:
        # Log full traceback in the Flask terminal
        app.logger.exception(
            "Error while processing sensor data"
        )

        return jsonify({
            "success": False,
            "error": "Internal server error. "
                     "Check the Flask terminal."
        }), 500

# ============================================================
# HEALTH CHECK
# ============================================================

@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "system": "Industrial AI Machine Monitoring",
        "status": "Server running",
        "ai_model": "Loaded",
        "api_endpoint": "/api/sensor"
    })

# ============================================================
# RUN SERVER
# ============================================================

if __name__ == "__main__":

    print()
    print("Starting Flask server...")
    print("Server address: http://127.0.0.1:5000")
    print("Sensor API: POST /api/sensor")
    print("Waiting for ESP32 sensor data...")
    print()

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False
    )