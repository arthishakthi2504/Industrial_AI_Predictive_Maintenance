
import streamlit as st
import pandas as pd
import requests
import time

# ============================================================
# CONFIGURATION
# ============================================================

API_URL = "https://industrial-ai-predictive-maintenance.onrender.com/api/data"

st.set_page_config(
    page_title="Industrial AI Monitoring",
    page_icon="🏭",
    layout="wide"
)

# ============================================================
# DASHBOARD HEADER
# ============================================================

st.title("🏭 Industrial AI Predictive Maintenance")
st.subheader("Live Machine Monitoring Dashboard")

st.markdown("---")

# ============================================================
# SIDEBAR SETTINGS
# ============================================================

st.sidebar.header("Dashboard Settings")

auto_refresh = st.sidebar.checkbox(
    "Auto refresh",
    value=True
)

refresh_seconds = st.sidebar.slider(
    "Refresh interval (seconds)",
    2, 30, 5
)

# ============================================================
# FETCH LIVE DATA FROM RENDER
# ============================================================

@st.cache_data(ttl=2)
def fetch_sensor_data():
    response = requests.get(API_URL, timeout=30)
    response.raise_for_status()

    result = response.json()

    if not result.get("success"):
        raise ValueError("Backend returned an unsuccessful response.")

    return result.get("data", [])

# ============================================================
# DISPLAY SENSOR DATA
# ============================================================

try:
    data = fetch_sensor_data()

    if data:
        df = pd.DataFrame(data)

        # Latest sensor reading
        latest = df.iloc[-1]

        st.subheader("Latest Sensor Readings")

        c1, c2, c3, c4 = st.columns(4)

        c1.metric(
            "🌡️ Temperature",
            f"{float(latest.get('temperature', 0)):.2f} °C"
        )

        c2.metric(
            "📳 Vibration",
            f"{float(latest.get('vibration', 0)):.2f} m/s²"
        )

        c3.metric(
            "⚡ Current",
            f"{float(latest.get('current', 0)):.2f} A"
        )

        c4.metric(
            "⚙️ RPM",
            f"{float(latest.get('rpm', 0)):.0f}"
        )

        st.caption(
            f"Last reading timestamp: {latest.get('timestamp', 'Unknown')}"
        )

        st.markdown("---")

        # ====================================================
        # MACHINE HEALTH
        # ====================================================

        st.subheader("Machine Health")

        health = str(
            latest.get("machine_health", "Unknown")
        ).upper()

        ml_status = str(
            latest.get("ml_status", "Unknown")
        ).upper()

        col1, col2 = st.columns(2)

        with col1:
            st.write("**Machine Health**")

            if health == "HEALTHY":
                st.success("✅ HEALTHY")
            elif health == "WARNING":
                st.warning("⚠️ WARNING")
            elif health == "CRITICAL":
                st.error("🚨 CRITICAL")
            else:
                st.info(health)

        with col2:
            st.write("**AI Classification**")

            if ml_status == "NORMAL":
                st.success("✅ NORMAL")
            elif ml_status == "ANOMALY":
                st.error("🚨 ANOMALY")
            else:
                st.info(ml_status)

        st.markdown("**Maintenance Recommendation**")
        st.info(
            latest.get(
                "maintenance",
                "No recommendation available."
            )
        )

        st.markdown("**Detected Evidence**")
        st.write(
            latest.get(
                "evidence",
                "No evidence available."
            )
        )

        st.markdown("---")

        # ====================================================
        # SENSOR HISTORY
        # ====================================================

        st.subheader("Sensor History")

        numeric_columns = [
            col for col in [
                "temperature",
                "vibration",
                "current",
                "rpm"
            ]
            if col in df.columns
        ]

        if numeric_columns:
            chart_df = df[numeric_columns].copy()

            st.line_chart(chart_df)

        st.markdown("---")

        # ====================================================
        # RECENT RECORDS
        # ====================================================

        st.subheader("Recent Sensor Records")

        st.dataframe(
            df.tail(20).iloc[::-1],
            use_container_width=True,
            hide_index=True
        )

        st.caption(
            f"Showing {len(df)} readings retrieved from the backend."
        )

    else:
        st.warning(
            "No sensor readings are available yet. "
            "Start your Wokwi simulation and wait for new data."
        )

except requests.exceptions.Timeout:
    st.error(
        "The backend took too long to respond. "
        "Please wait a moment and refresh."
    )

except requests.exceptions.RequestException as e:
    st.error(
        f"Could not connect to the backend: {e}"
    )

except (ValueError, TypeError, KeyError) as e:
    st.error(
        f"Could not process the sensor data: {e}"
    )

# ============================================================
# AUTO REFRESH
# ============================================================

if auto_refresh:
    time.sleep(refresh_seconds)
    st.rerun()