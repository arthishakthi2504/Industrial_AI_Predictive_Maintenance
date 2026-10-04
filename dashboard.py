import streamlit as st
import pandas as pd
import requests
import time
import os

# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Industrial AI Monitoring",
    page_icon="🏭",
    layout="wide"
)

st.title("🏭 Industrial AI Predictive Maintenance")
st.subheader("Live Machine Monitoring Dashboard")

# ============================================================
# FLASK SERVER
# ============================================================

DEFAULT_API_URL = (
    "https://industrial-ai-predictive-maintenance.onrender.com"
)

API_URL = os.environ.get(
    "API_URL",
    DEFAULT_API_URL
)

DATA_ENDPOINT = f"{API_URL}/api/data"

# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.header("Dashboard Settings")

auto_refresh = st.sidebar.checkbox(
    "Auto refresh",
    value=True
)

refresh_seconds = st.sidebar.slider(
    "Refresh interval (seconds)",
    2,
    30,
    5
)

st.sidebar.markdown("---")

st.sidebar.write("Backend:")
st.sidebar.code(API_URL)

# ============================================================
# GET DATA FROM FLASK / POSTGRESQL
# ============================================================

def get_sensor_data():

    try:
        response = requests.get(
            DATA_ENDPOINT,
            timeout=15
        )

        response.raise_for_status()

        result = response.json()

        if not result.get("success"):
            return None, "Backend returned an error."

        records = result.get("data", [])

        if not records:
            return pd.DataFrame(), None

        df = pd.DataFrame(records)

        if "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(
                df["timestamp"],
                errors="coerce"
            )

        return df, None

    except requests.exceptions.RequestException as e:
        return None, f"Could not connect to backend: {e}"

    except Exception as e:
        return None, f"Could not process sensor data: {e}"

# ============================================================
# LOAD DATA
# ============================================================

df, error = get_sensor_data()

if error:

    st.error(error)

    st.info(
        "Make sure your Render Flask service is running."
    )

else:

    if df is None or df.empty:

        st.info(
            "Waiting for sensor data from ESP32..."
        )

    else:

        # ----------------------------------------------------
        # LATEST READING
        # ----------------------------------------------------

        latest = df.iloc[-1]

        st.markdown("---")
        st.subheader("📡 Latest Sensor Readings")

        c1, c2, c3, c4 = st.columns(4)

        temperature = float(
            latest.get("temperature", 0)
        )

        vibration = float(
            latest.get("vibration", 0)
        )

        current = float(
            latest.get("current", 0)
        )

        rpm = float(
            latest.get("rpm", 0)
        )

        c1.metric(
            "🌡️ Temperature",
            f"{temperature:.2f} °C"
        )

        c2.metric(
            "📳 Vibration",
            f"{vibration:.2f} m/s²"
        )

        c3.metric(
            "⚡ Current",
            f"{current:.2f} A"
        )

        c4.metric(
            "⚙️ RPM",
            f"{rpm:.0f}"
        )

        # ----------------------------------------------------
        # MACHINE HEALTH
        # ----------------------------------------------------

        st.markdown("---")
        st.subheader("🤖 Machine Health")

        health = str(
            latest.get(
                "machine_health",
                "UNKNOWN"
            )
        )

        ml_status = str(
            latest.get(
                "ml_status",
                "UNKNOWN"
            )
        )

        maintenance = str(
            latest.get(
                "maintenance",
                "No recommendation available."
            )
        )

        evidence = str(
            latest.get(
                "evidence",
                "No evidence available."
            )
        )

        h1, h2 = st.columns(2)

        with h1:

            st.write("### Machine Health")

            if health.upper() == "HEALTHY":

                st.success(
                    "🟢 MACHINE HEALTHY"
                )

            elif health.upper() == "WARNING":

                st.warning(
                    "🟡 MACHINE WARNING"
                )

            elif health.upper() == "CRITICAL":

                st.error(
                    "🔴 MACHINE CRITICAL"
                )

            else:

                st.info(
                    f"Machine status: {health}"
                )

        with h2:

            st.write("### AI Classification")

            if ml_status.upper() == "NORMAL":

                st.success(
                    "🟢 AI: NORMAL"
                )

            elif ml_status.upper() == "ANOMALY":

                st.error(
                    "🔴 AI: ANOMALY"
                )

            else:

                st.info(
                    f"AI Status: {ml_status}"
                )

        # ----------------------------------------------------
        # MAINTENANCE INFORMATION
        # ----------------------------------------------------

        st.markdown("---")
        st.subheader("🔧 Maintenance Analysis")

        m1, m2 = st.columns(2)

        with m1:

            st.write("**Detected Evidence:**")

            st.info(evidence)

        with m2:

            st.write("**Recommended Action:**")

            if health.upper() == "CRITICAL":

                st.error(maintenance)

            elif health.upper() == "WARNING":

                st.warning(maintenance)

            else:

                st.success(maintenance)

        # ----------------------------------------------------
        # SENSOR HISTORY
        # ----------------------------------------------------

        st.markdown("---")
        st.subheader("📈 Sensor History")

        numeric_columns = [
            "temperature",
            "vibration",
            "current",
            "rpm"
        ]

        available_columns = [
            col
            for col in numeric_columns
            if col in df.columns
        ]

        if available_columns:

            chart_df = df[
                available_columns
            ].copy()

            st.line_chart(chart_df)

        # ----------------------------------------------------
        # RECORD COUNT
        # ----------------------------------------------------

        st.markdown("---")

        total_records = len(df)

        st.metric(
            "📊 Records Loaded",
            total_records
        )

        # ----------------------------------------------------
        # RECENT RECORDS
        # ----------------------------------------------------

        st.subheader("📋 Recent Sensor Records")

        display_columns = [
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

        available_display_columns = [
            col
            for col in display_columns
            if col in df.columns
        ]

        recent_df = df[
            available_display_columns
        ].tail(20).copy()

        st.dataframe(
            recent_df,
            use_container_width=True,
            hide_index=True
        )

        # ----------------------------------------------------
        # LAST UPDATE
        # ----------------------------------------------------

        if "timestamp" in latest:

            st.caption(
                f"Last sensor reading: "
                f"{latest['timestamp']}"
            )

# ============================================================
# AUTO REFRESH
# ============================================================

if auto_refresh:

    time.sleep(refresh_seconds)

    st.rerun()