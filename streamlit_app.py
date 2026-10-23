"""Canonical AYUSARTHI Streamlit entrypoint.

Run from the repository root with:
    python -m streamlit run streamlit_app.py

This wrapper keeps branding/configuration in one place while reusing the existing
frontend implementation in ``frontend/app.py``.
"""

import os
from pathlib import Path

import streamlit as st


ROOT_DIR = Path(__file__).resolve().parent
LOGO_PATH = ROOT_DIR / "frontend" / "ayusarthi_logo.jpeg"
PAGE_ICON = LOGO_PATH if LOGO_PATH.is_file() else "🌿"

# Configure the browser tab before importing the rest of the Streamlit UI.
st.set_page_config(
    page_title="AYUSARTHI AI",
    page_icon=PAGE_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)

from frontend import app as ui  # noqa: E402  (import after page configuration)


# Make .env.example/environment configuration meaningful without adding a dotenv
# dependency. Defaults preserve the existing local prototype behavior.
ui.SENSOR_URL = os.environ.get("SENSOR_URL", ui.SENSOR_URL).strip() or ui.SENSOR_URL
ui.CHAT_URL = os.environ.get("N8N_CHAT_URL", ui.CHAT_URL).strip() or ui.CHAT_URL


def main():
    st.markdown(ui.CSS, unsafe_allow_html=True)
    ui.initialize_session()

    logo, logo_warning = ui.prepare_logo()
    ui.render_splash(logo)

    sensor = ui.get_sensor_status()
    ui.render_sidebar(logo, sensor, logo_warning)
    ui.render_topbar(sensor)

    page = st.session_state.page
    if page == "Chat":
        ui.render_chat_page(logo)
    elif page == "Monitoring":
        ui.render_monitoring_page(sensor)
    elif page == "Caregiver":
        ui.render_caregiver_page()
    elif page == "Alerts":
        ui.render_alerts_page()
    else:
        ui.render_about_page()


if __name__ == "__main__":
    main()
