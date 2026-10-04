
from flask import Flask, request, jsonify
import pandas as pd
import joblib
import os
import math
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

MODEL_FILE = os.path.join(
    BASE_DIR, "ml", "anomaly_model.pkl"
)

DATABASE_URL = os.environ.get("DATABASE_URL")

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

# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_db_connection():
    if not DATABASE_URL:
        raise RuntimeError(
            "DATABASE_URL environment variable is missing."
        )

    return psycopg2.connect(DATABASE_URL)


# ============================================================
# CREATE DATABASE TABLE
# ============================================================

def initialize_database():
    create_table_sql = """
        CREATE TABLE IF NOT EXISTS sensor_readings (
            id SERIAL PRIMARY KEY,
            timestamp TIMESTAMP NOT NULL,
            temperature DOUBLE PRECISION NOT NULL,
            vibration DOUBLE PRECISION NOT NULL,
            current DOUBLE PRECISION NOT NULL,
            rpm DOUBLE PRECISION NOT NULL,
            ml_status TEXT NOT NULL,
            machine_health TEXT NOT NULL,
            maintenance TEXT NOT NULL,
            evidence TEXT NOT NULL
        );
    """

    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(create_table_sql)

    print("PostgreSQL database initialized successfully.")


# Initialize the database when the application starts.
initialize_database()

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

    ml_status = (
        "ANOMALY" if prediction == -1 else "NORMAL"
    )

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
        maintenance = (
            "Sensor condition requires inspection."
        )

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
# RECEIVE SENSOR DATA FROM WOKWI
# ============================================================

@app.route("/api/sensor", methods=["POST"])
def receive_sensor_data():

    if not request.is_json:
        return jsonify({
            "success": False,
            "error": "Content-Type must be application/json"
        }), 400

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "success": False,
            "error": "Invalid or missing JSON object"
        }), 400

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
        result = analyze_machine(
            temperature,
            vibration,
            current,
            rpm
        )

        timestamp = datetime.utcnow()

        # Save the new reading in PostgreSQL.
        insert_sql = """
            INSERT INTO sensor_readings (
                timestamp,
                temperature,
                vibration,
                current,
                rpm,
                ml_status,
                machine_health,
                maintenance,
                evidence
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id;
        """

        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    insert_sql,
                    (
                        timestamp,
                        temperature,
                        vibration,
                        current,
                        rpm,
                        result["ml_status"],
                        result["machine_health"],
                        result["maintenance"],
                        result["evidence"]
                    )
                )

                reading_id = cursor.fetchone()[0]

        row = {
            "id": reading_id,
            "timestamp": timestamp.isoformat(),
            "temperature": temperature,
            "vibration": vibration,
            "current": current,
            "rpm": rpm,
            **result
        }

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
        print(f"Action      : {result['maintenance']}")
        print("Saved to PostgreSQL.")
        print("==============================================")

        return jsonify({
            "success": True,
            **row
        }), 200

    except Exception:
        app.logger.exception(
            "Error while processing sensor data"
        )

        return jsonify({
            "success": False,
            "error": "Could not process or save sensor data."
        }), 500

# ============================================================
# GET SENSOR DATA FOR STREAMLIT
# ============================================================

@app.route("/api/data", methods=["GET"])
def get_sensor_data():

    try:
        limit = request.args.get("limit", default=100, type=int)

        if limit is None or limit < 1:
            return jsonify({
                "success": False,
                "error": "Limit must be a positive number."
            }), 400

        limit = min(limit, 1000)

        select_sql = """
            SELECT
                id,
                timestamp,
                temperature,
                vibration,
                current,
                rpm,
                ml_status,
                machine_health,
                maintenance,
                evidence
            FROM sensor_readings
            ORDER BY id DESC
            LIMIT %s;
        """

        with get_db_connection() as conn:
            with conn.cursor(
                cursor_factory=RealDictCursor
            ) as cursor:
                cursor.execute(select_sql, (limit,))
                rows = cursor.fetchall()

        # Return oldest-to-newest within the selected records.
        rows = list(reversed(rows))

        for row in rows:
            row["timestamp"] = row["timestamp"].isoformat()

        return jsonify({
            "success": True,
            "count": len(rows),
            "data": rows
        }), 200

    except Exception:
        app.logger.exception(
            "Error retrieving sensor data"
        )

        return jsonify({
            "success": False,
            "error": "Could not retrieve sensor data."
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
        "database": "PostgreSQL",
        "sensor_endpoint": "/api/sensor",
        "data_endpoint": "/api/data"
    })

# ============================================================
# RUN SERVER
# ============================================================

if __name__ == "__main__":

    print("Starting Flask server...")
    print("Sensor API: POST /api/sensor")
    print("Data API: GET /api/data")
    print("Waiting for ESP32 sensor data...")

    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000))
    )