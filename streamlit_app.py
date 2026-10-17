"""Canonical AYUSARTHI Streamlit entrypoint.

Run from the repository root with:
    python -m streamlit run streamlit_app.py

This wrapper keeps branding/configuration in one place while reusing the existing
frontend implementation in ``frontend/app.py``.
"""

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


def main():
    ui.main(configure_page=False)


if __name__ == "__main__":
    main()
