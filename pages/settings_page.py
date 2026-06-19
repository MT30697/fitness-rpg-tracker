"""Settings - user profile, nutrition targets, workout schedule."""
from __future__ import annotations

from datetime import date, datetime

import streamlit as st

from components.ui import bottom_tab_bar, decimal_input, page_header
from utils import gsheets_backend as GS
from utils import constants as C
from utils import data_manager as DM

page_header("Settings", "⚙️", "Your profile, targets and schedule.")

settings = DM.load_settings()

# ----------------------------------------------------------------------
# User Profile
# ----------------------------------------------------------------------
st.markdown("#### User Profile")
with st.form("profile_form"):
    col1, col2 = st.columns(2)
    with col1:
        height = decimal_input("Height (cm)", value=float(settings.get("height_cm") or 179), key="set_height")
        current_weight = decimal_input("Current Weight (kg)", value=float(settings.get("current_weight_kg") or 86), key="set_cw")
        goal_weight = decimal_input("Goal Weight (kg)", value=float(settings.get("goal_weight_kg") or 80), key="set_gw")
    with col2:
        waist = decimal_input("Waist (cm, optional)", value=float(settings.get("waist_cm") or 0), key="set_waist")
        try:
            default_start = datetime.fromisoformat(settings.get("start_date")).date()
        except Exception:
            default_start = date.today()
        start_date = st.date_input("Start Date", value=default_start)

    profile_submit = st.form_submit_button("Save Profile", use_container_width=True)
    if profile_submit:
        settings["height_cm"] = height
        settings["current_weight_kg"] = current_weight
        settings["goal_weight_kg"] = goal_weight
        settings["waist_cm"] = waist if waist else None
        settings["start_date"] = start_date.isoformat()
        DM.save_settings(settings)
        st.success("Profile saved.")
        st.rerun()

st.divider()

# ----------------------------------------------------------------------
# Nutrition Targets
# ----------------------------------------------------------------------
st.markdown("#### Nutrition Targets")
targets = settings.get("nutrition_targets", C.DEFAULT_SETTINGS["nutrition_targets"])
with st.form("nutrition_targets_form"):
    n1, n2, n3, n4 = st.columns(4)
    with n1:
        cal_target = st.number_input("Calories", min_value=0, step=10, value=int(targets.get("calories", 2400)))
    with n2:
        protein_target = st.number_input("Protein (g)", min_value=0, step=5, value=int(targets.get("protein", 205)))
    with n3:
        carb_target = st.number_input("Carbs (g)", min_value=0, step=5, value=int(targets.get("carbs", 267)))
    with n4:
        fat_target = st.number_input("Fat (g)", min_value=0, step=5, value=int(targets.get("fat", 67)))

    nutrition_submit = st.form_submit_button("Save Nutrition Targets", use_container_width=True)
    if nutrition_submit:
        settings["nutrition_targets"] = {
            "calories": cal_target, "protein": protein_target, "carbs": carb_target, "fat": fat_target,
        }
        DM.save_settings(settings)
        st.success("Nutrition targets saved.")
        st.rerun()

st.divider()

# ----------------------------------------------------------------------
# Workout Schedule
# ----------------------------------------------------------------------
st.markdown("#### Workout Schedule")
with st.form("schedule_form"):
    col1, col2 = st.columns(2)
    with col1:
        cardio_time_str = settings.get("cardio_reminder_time", "06:00")
        cardio_time = st.time_input(
            "Cardio Reminder", value=datetime.strptime(cardio_time_str, "%H:%M").time()
        )
    with col2:
        gym_time_str = settings.get("gym_reminder_time", "14:00")
        gym_time = st.time_input(
            "Gym Reminder", value=datetime.strptime(gym_time_str, "%H:%M").time()
        )

    workout_days = st.multiselect("Workout Days", C.WEEKDAYS, default=settings.get("workout_days", []))

    schedule_submit = st.form_submit_button("Save Schedule", use_container_width=True)
    if schedule_submit:
        settings["cardio_reminder_time"] = cardio_time.strftime("%H:%M")
        settings["gym_reminder_time"] = gym_time.strftime("%H:%M")
        settings["workout_days"] = workout_days
        DM.save_settings(settings)
        st.success("Schedule saved.")
        st.rerun()

st.divider()
storage_label = "📡 Data syncs to Google Sheets." if GS.is_enabled() else "💾 Data is stored locally on this device as CSV/JSON files."
st.caption(storage_label)

bottom_tab_bar(active="more")
