"""
Fitness RPG Tracker - entry point.

Run with:  streamlit run app.py
"""
import streamlit as st

from utils.data_manager import ensure_data_files
from components.ui import inject_pwa_meta, load_css

st.set_page_config(
    page_title="Fitness RPG Tracker",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Create data folder/files (local mode) or worksheets (Sheets mode) on
# first run, and verify on every run.
ensure_data_files()

load_css()
inject_pwa_meta()

# Navigation is via the bottom tab bar (components.ui.bottom_tab_bar),
# not the Streamlit sidebar — every page calls it directly. st.Page is
# still required so st.navigation knows the routes exist and st.page_link
# (used inside the tab bar) can link to them.
pages = [
    st.Page("pages/dashboard.py", title="Dashboard", icon="🏠", default=True),
    st.Page("pages/exercise_library.py", title="Exercise Library", icon="📚"),
    st.Page("pages/workout_log.py", title="Workout Log", icon="💪"),
    st.Page("pages/cardio.py", title="Cardio", icon="🏃"),
    st.Page("pages/nutrition.py", title="Nutrition", icon="🍽️"),
    st.Page("pages/body_progress.py", title="Body Progress", icon="📈"),
    st.Page("pages/rpg_system.py", title="RPG System", icon="🎮"),
    st.Page("pages/settings_page.py", title="Settings", icon="⚙️"),
    st.Page("pages/more.py", title="More", icon="⋯"),
]

try:
    # position="hidden" stops Streamlit from rendering its own sidebar nav
    # list at all (newer Streamlit versions). On older versions without
    # this parameter, the CSS rule hiding [data-testid="stSidebar"] above
    # still achieves the same visual result either way.
    nav = st.navigation(pages, position="hidden")
except TypeError:
    nav = st.navigation(pages)
nav.run()
