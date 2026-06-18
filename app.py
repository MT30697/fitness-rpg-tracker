"""
Fitness RPG Tracker - entry point.

Run with:  streamlit run app.py
"""
import streamlit as st

from utils.data_manager import ensure_data_files
from utils import gsheets_backend as GS
from components.ui import load_css

st.set_page_config(
    page_title="Fitness RPG Tracker",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Create data folder/files (local mode) or worksheets (Sheets mode) on
# first run, and verify on every run.
ensure_data_files()

load_css()

pages = [
    st.Page("pages/dashboard.py", title="Dashboard", icon="🏠", default=True),
    st.Page("pages/exercise_library.py", title="Exercise Library", icon="📚"),
    st.Page("pages/workout_log.py", title="Workout Log", icon="💪"),
    st.Page("pages/cardio.py", title="Cardio", icon="🏃"),
    st.Page("pages/nutrition.py", title="Nutrition", icon="🍽️"),
    st.Page("pages/body_progress.py", title="Body Progress", icon="📈"),
    st.Page("pages/rpg_system.py", title="RPG System", icon="🎮"),
    st.Page("pages/settings_page.py", title="Settings", icon="⚙️"),
]

nav = st.navigation(pages)

with st.sidebar:
    st.markdown("### 🎮 Fitness RPG Tracker")
    st.caption("Level up your real life.")
    storage_label = "📡 Cloud sync — Google Sheets" if GS.is_enabled() else "💾 Local storage"
    st.caption(storage_label)
    st.divider()

nav.run()
