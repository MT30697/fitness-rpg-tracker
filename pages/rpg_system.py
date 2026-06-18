"""RPG System - level, XP, streaks and achievements."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from components.ui import achievement_tile, level_ring, page_header, progress_bar
from utils import calculations as calc
from utils import constants as C
from utils import data_manager as DM
from utils import rpg_engine as RPG

page_header("RPG System", "🎮", "Your character sheet.")

settings = DM.load_settings()
rpg_state = RPG.load_rpg_state()
level_info = RPG.get_level_info(rpg_state.get("xp", 0))

workout_df = DM.load_workout_log()
cardio_df = DM.load_cardio_log()
nutrition_df = DM.load_nutrition_log()

# ----------------------------------------------------------------------
# Level / XP
# ----------------------------------------------------------------------
c1, c2 = st.columns([1, 2])
with c1:
    st.markdown('<div class="rpg-card" style="display:flex; flex-direction:column; align-items:center;"><div class="rpg-card-tag" style="width:100%;">CHARACTER LEVEL</div>', unsafe_allow_html=True)
    level_ring(level_info["level"], level_info["xp_into_level"], C.XP_PER_LEVEL, level_info["xp"], size="lg")
    st.markdown("</div>", unsafe_allow_html=True)
with c2:
    st.markdown("##### Progress to Next Level")
    progress_bar(
        f"Level {level_info['level']} → {level_info['level'] + 1}",
        level_info["xp_into_level"], C.XP_PER_LEVEL, " XP",
    )
    st.caption(f"{level_info['xp_needed_next']} XP needed for the next level.")

    st.markdown("##### XP Rules")
    rule_labels = {
        "workout_logged": "Workout Logged",
        "cardio_logged": "Cardio Logged",
        "protein_goal_met": "Protein Goal Met",
        "body_checkin": "Body Check-in",
        "new_pr": "New PR",
        "weekly_goal_completed": "Weekly Goal Completed",
    }
    rule_cols = st.columns(3)
    for i, (key, amount) in enumerate(C.XP_RULES.items()):
        with rule_cols[i % 3]:
            st.caption(f"**{rule_labels.get(key, key)}**: +{amount} XP")

st.divider()

# ----------------------------------------------------------------------
# Streaks
# ----------------------------------------------------------------------
st.markdown("#### Streaks")

workout_dates = []
if not workout_df.empty:
    workout_dates = pd.to_datetime(workout_df["date"], errors="coerce").dropna().dt.date.tolist()
workout_streak = calc.compute_streak(workout_dates)

cardio_dates = []
if not cardio_df.empty:
    cardio_dates = pd.to_datetime(cardio_df["date"], errors="coerce").dropna().dt.date.tolist()
cardio_streak = calc.compute_streak(cardio_dates)

protein_met_days = []
if not nutrition_df.empty:
    targets = settings.get("nutrition_targets", C.DEFAULT_SETTINGS["nutrition_targets"])
    ndf = nutrition_df.copy()
    ndf["date_only"] = pd.to_datetime(ndf["date"], errors="coerce").dt.date
    daily_protein = ndf.groupby("date_only")["protein"].sum()
    protein_met_days = [d for d, p in daily_protein.items() if p >= targets.get("protein", 0)]
protein_streak = calc.compute_streak(protein_met_days)

s1, s2, s3 = st.columns(3)
s1.metric("🏋️ Workout Streak", f"{workout_streak} days")
s2.metric("🏃 Cardio Streak", f"{cardio_streak} days")
s3.metric("🍗 Protein Streak", f"{protein_streak} days")

st.divider()

# ----------------------------------------------------------------------
# Achievements
# ----------------------------------------------------------------------
st.markdown("#### Achievements")
achievements = RPG.load_achievements()
unlocked_list = [a for a in achievements.values() if a.get("unlocked")]
locked_list = [a for a in achievements.values() if not a.get("unlocked")]

st.progress(len(unlocked_list) / max(len(achievements), 1))
st.caption(f"{len(unlocked_list)} / {len(achievements)} achievements unlocked")

st.write("")
grid_cols = st.columns(5)
all_sorted = unlocked_list + locked_list
for i, ach in enumerate(all_sorted):
    with grid_cols[i % 5]:
        achievement_tile(ach["name"], ach["icon"], ach["description"], ach.get("unlocked", False), ach.get("unlocked_date"))
