"""More — secondary destinations not on the main tab bar, plus app info."""
import streamlit as st

from components.ui import bottom_tab_bar, page_header
from utils import gsheets_backend as GS

page_header("More", "🧩")

st.markdown('<div class="more-row">', unsafe_allow_html=True)
st.page_link("pages/exercise_library.py", label="📚  Exercise Library", icon=None)
st.markdown("</div>", unsafe_allow_html=True)

st.markdown('<div class="more-row">', unsafe_allow_html=True)
st.page_link("pages/body_progress.py", label="📈  Body Progress", icon=None)
st.markdown("</div>", unsafe_allow_html=True)

st.markdown('<div class="more-row">', unsafe_allow_html=True)
st.page_link("pages/rpg_system.py", label="🎮  RPG System", icon=None)
st.markdown("</div>", unsafe_allow_html=True)

st.markdown('<div class="more-row">', unsafe_allow_html=True)
st.page_link("pages/settings_page.py", label="⚙️  Settings", icon=None)
st.markdown("</div>", unsafe_allow_html=True)

st.write("")
storage_label = "📡 Cloud sync — Google Sheets" if GS.is_enabled() else "💾 Local storage"
st.caption(storage_label)
st.caption("Fitness RPG Tracker — level up your real life.")

bottom_tab_bar(active="more")
