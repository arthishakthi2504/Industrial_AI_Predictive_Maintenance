
import streamlit as st
import pandas as pd
import requests
import time
from datetime import datetime

# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Industrial AI Predictive Maintenance",
    page_icon="🏭",
    layout="wide"
)

API_URL = (
    "https://industrial-ai-predictive-maintenance"
    ".onrender.com/api/data"
)

# ============================================================
# CUSTOM DESIGN
# ============================================================

st.markdown("""
<style>
    .main-title {
        font-size: 32px;
        font-weight: bold;
        color: #1976D2;
        text-align: center;
    }

    .subtitle {
        text-align: center;
        color: gray;
        font-size: 16px;
    }

    .alert-box {
        padding: 18px;
        border-radius: 10px;
        text-align: center;
        font-size: 22px;
        font-weight: bold;
        margin-bottom: 15px;
    }

    .healthy {
        background-color: #d4edda;
        color: #155724;
        border: 1px solid #28a745;
    }

    .warning {
        background-color: #fff3cd;
        color: #856404;
        border: 1px solid #ffc107;
    }

    .critical {
        background-color: #f8d7da;
        color: #721c24;
        border: 1px solid #dc3545;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# HEADER
# ============================================================

st.markdown(
    '<div class="main-title">🏭 Industrial AI Predictive Maintenance</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">Live Machine Monitoring and Anomaly Detection</div>',
    unsafe_allow_html=True
)

st.markdown("---")

# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title("⚙️ Dashboard Settings")

auto_refresh = st.sidebar.checkbox(
    "Enable Auto Refresh",
    value=True
)

refresh_seconds = st.sidebar.slider(
    "Refresh Interval (seconds)",
    min_value=2,
    max_value=30,
    value=5
)

st.sidebar.markdown("---")
st.sidebar.info(
    "Data Source: Wokwi ESP32 → Render Flask API"
)

if st.sidebar.button("🔄 Refresh Now"):
    st.cache_data.clear()
    st.rerun()

# ============================================================
# FETCH LIVE DATA
# ============================================================

@st.cache_data(ttl=2)
def fetch_sensor_data():
    response = requests.get(
        API_URL,
        timeout=30
    )
    response.raise_for_status()

    result = response.json()

    if not result.get("success"):
        raise ValueError("Backend returned unsuccessful response")

    return result.get("data", [])

# ============================================================
# MAIN DASHBOARD
# ============================================================

try:
    data = fetch_sensor_data()

    if not data:
        st.warning(
            "⏳ No sensor data available. "
            "Start the Wokwi simulation."
        )

    else:
        df = pd.DataFrame(data)

        # Convert sensor columns to numeric values
        sensor_columns = [
            "temperature",
            "vibration",
            "current",
            "rpm"
        ]

        for col in sensor_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(
                    df[col],
                    errors="coerce"
                )

        latest = df.iloc[-1]

        # ====================================================
        # MACHINE STATUS
        # ====================================================

        st.subheader("🚨 Machine Health Status")

        health = str(
            latest.get("machine_health", "UNKNOWN")
        ).upper()

        ml_status = str(
            latest.get("ml_status", "UNKNOWN")
        ).upper()

        if health == "HEALTHY":
            st.markdown(
                '<div class="alert-box healthy">'
                '🟢 MACHINE HEALTHY — NORMAL OPERATION'
                '</div>',
                unsafe_allow_html=True
            )

        elif health == "WARNING":
            st.markdown(
                '<div class="alert-box warning">'
                '🟡 WARNING — INSPECTION RECOMMENDED'
                '</div>',
                unsafe_allow_html=True
            )

        elif health == "CRITICAL":
            st.markdown(
                '<div class="alert-box critical">'
                '🔴 CRITICAL — MAINTENANCE REQUIRED'
                '</div>',
                unsafe_allow_html=True
            )

        else:
            st.info(f"Machine Health: {health}")

        # AI alert panel
        if ml_status == "ANOMALY":
            st.error(
                "🚨 AI ANOMALY ALERT: "
                "The AI model detected abnormal machine behavior."
            )
        elif ml_status == "NORMAL":
            st.success(
                "✅ AI STATUS: No anomaly detected in the latest reading."
            )
        else:
            st.info(f"AI Classification: {ml_status}")

        st.markdown("---")

        # ====================================================
        # LIVE SENSOR METRICS
        # ====================================================

        st.subheader("📡 Live Sensor Readings")

        c1, c2, c3, c4 = st.columns(4)

        c1.metric(
            "🌡️ Temperature",
            f"{latest.get('temperature', 0):.2f} °C"
        )

        c2.metric(
            "📳 Vibration",
            f"{latest.get('vibration', 0):.2f} m/s²"
        )

        c3.metric(
            "⚡ Current",
            f"{latest.get('current', 0):.2f} A"
        )

        c4.metric(
            "⚙️ RPM",
            f"{latest.get('rpm', 0):.0f}"
        )

        st.caption(
            "Latest reading: "
            + str(latest.get("timestamp", "Unknown"))
        )

        st.markdown("---")

        # ====================================================
        # MAINTENANCE RECOMMENDATION
        # ====================================================

        st.subheader("🛠️ Maintenance Recommendation")

        maintenance = latest.get(
            "maintenance",
            "No recommendation available."
        )

        evidence = latest.get(
            "evidence",
            "No evidence available."
        )

        st.info(f"**Recommended Action:** {maintenance}")

        st.write(f"**Detected Evidence:** {evidence}")

        st.markdown("---")

        # ====================================================
        # SENSOR GRAPHS
        # ====================================================

        st.subheader("📊 Sensor Monitoring Graphs")

        graph_tabs = st.tabs([
            "🌡️ Temperature",
            "📳 Vibration",
            "⚡ Current",
            "⚙️ RPM"
        ])

        graph_settings = [
            ("temperature", "Temperature (°C)"),
            ("vibration", "Vibration (m/s²)"),
            ("current", "Current (A)"),
            ("rpm", "RPM")
        ]

        for tab, (column, label) in zip(
            graph_tabs,
            graph_settings
        ):
            with tab:
                if column in df.columns:
                    chart_data = df[[column]].dropna()
                    st.line_chart(
                        chart_data,
                        height=350,
                        y_label=label
                    )
                else:
                    st.info(
                        f"No {label.lower()} data available."
                    )

        st.markdown("---")

        # ====================================================
        # RECENT SENSOR RECORDS
        # ====================================================

        st.subheader("📋 Recent Sensor Records")

        display_columns = [
            "timestamp",
            "temperature",
            "vibration",
            "current",
            "rpm",
            "ml_status",
            "machine_health"
        ]

        available_columns = [
            col for col in display_columns
            if col in df.columns
        ]

        st.dataframe(
            df[available_columns].tail(20).iloc[::-1],
            use_container_width=True,
            hide_index=True
        )

        # ====================================================
        # SUMMARY
        # ====================================================

        st.markdown("---")
        st.subheader("📈 Monitoring Summary")

        total_readings = len(df)

        anomaly_count = (
            df["ml_status"].astype(str).str.upper() == "ANOMALY"
        ).sum() if "ml_status" in df.columns else 0

        normal_count = (
            df["ml_status"].astype(str).str.upper() == "NORMAL"
        ).sum() if "ml_status" in df.columns else 0

        s1, s2, s3 = st.columns(3)

        s1.metric(
            "Total Readings",
            total_readings
        )

        s2.metric(
            "Normal Readings",
            int(normal_count)
        )

        s3.metric(
            "Anomaly Readings",
            int(anomaly_count)
        )

        st.caption(
            "Summary covers the readings returned by the backend, "
            "up to the latest 100 records."
        )

except requests.exceptions.Timeout:
    st.error(
        "⏳ Backend response timed out. "
        "Wait a moment and refresh."
    )

except requests.exceptions.RequestException as e:
    st.error(
        f"❌ Could not connect to Render backend: {e}"
    )

except (ValueError, TypeError, KeyError) as e:
    st.error(
        f"❌ Could not process sensor data: {e}"
    )

# ============================================================
# AUTO REFRESH
# ============================================================

if auto_refresh:
    time.sleep(refresh_seconds)
    st.rerun()