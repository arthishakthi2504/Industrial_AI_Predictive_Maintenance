
import streamlit as st
import pandas as pd
import requests
import time
from pathlib import Path

st.set_page_config(
    page_title="Industrial AI Monitoring",
    page_icon="🏭",
    layout="wide"
)

st.title("🏭 Industrial AI Predictive Maintenance")
st.subheader("Live Machine Monitoring Dashboard")

CSV_FILE = Path(__file__).parent / "data" / "live_data.csv"

st.sidebar.header("Dashboard Settings")
auto_refresh = st.sidebar.checkbox("Auto refresh", value=True)
refresh_seconds = st.sidebar.slider(
    "Refresh interval (seconds)", 2, 30, 5
)

st.markdown("---")

if CSV_FILE.exists():
    try:
        df = pd.read_csv(CSV_FILE)

        if not df.empty:
            latest = df.iloc[-1]

            # Adjust these column names if your CSV uses different names.
            st.subheader("Latest Sensor Readings")

            c1, c2, c3, c4 = st.columns(4)

            c1.metric("Temperature", f"{latest.get('temperature', 0)} °C")
            c2.metric("Vibration", f"{latest.get('vibration', 0)} m/s²")
            c3.metric("Current", f"{latest.get('current', 0)} A")
            c4.metric("RPM", f"{latest.get('rpm', 0)}")

            st.markdown("---")
            st.subheader("Machine Health")

            health = str(latest.get("machine_health", "Unknown"))
            ml_status = str(latest.get("ml_status", "Unknown"))

            st.write("**Machine Health:**", health)
            st.write("**AI Classification:**", ml_status)

            if health.upper() == "HEALTHY":
                st.success("Machine is operating normally.")
            elif health.upper() == "WARNING":
                st.warning("Potential abnormal behavior detected.")
            elif health.upper() == "CRITICAL":
                st.error("Critical machine condition detected.")
            else:
                st.info("Machine status is not available.")

            st.markdown("---")
            st.subheader("Sensor History")

            numeric_columns = [
                col for col in ["temperature", "vibration", "current", "rpm"]
                if col in df.columns
            ]

            if numeric_columns:
                st.line_chart(df[numeric_columns])

            st.markdown("---")
            st.subheader("Recent Sensor Records")
            st.dataframe(df.tail(20), use_container_width=True)

        else:
            st.info("CSV is empty. Waiting for sensor data.")

    except Exception as e:
        st.error(f"Could not read sensor data: {e}")
else:
    st.warning("Sensor data file not found. Waiting for data.")

if auto_refresh:
    time.sleep(refresh_seconds)
    st.rerun()