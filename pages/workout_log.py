"""Workout Log - log sets, track PRs and progressive overload."""
from __future__ import annotations

from datetime import date

import pandas as pd
import plotly.express as px
import streamlit as st

from components.ui import bottom_tab_bar, page_header, render_badges, status_to_style
from utils import calculations as calc
from utils import constants as C
from utils import data_manager as DM
from utils import rpg_engine as RPG
from utils import workout_actions as WA

page_header("Workout Log", "💪", "Log your sets, chase PRs, beat last time.")

st.page_link("pages/workout_templates.py", label="🗂️ Tập theo lịch cố định? Dùng Workout Templates để log nhanh hơn", icon=None)
st.write("")

library_df = DM.load_exercise_library()
workout_df = DM.load_workout_log()

if library_df.empty:
    st.warning("Add exercises in the Exercise Library page first, then come back here to log a workout.")

# ----------------------------------------------------------------------
# Log a workout entry
# ----------------------------------------------------------------------
with st.expander("➕ Log Workout Entry", expanded=True):
    muscle_choice = st.selectbox("Muscle Group", C.MUSCLE_GROUPS, key="log_muscle")
    available_exercises = (
        library_df[library_df["muscle_group"] == muscle_choice]["exercise_name"].tolist()
        if not library_df.empty else []
    )

    with st.form("workout_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            log_date = st.date_input("Date", value=date.today())
            exercise = st.selectbox("Exercise", available_exercises) if available_exercises else st.text_input("Exercise (add to library first)")
            sets = st.number_input("Sets", min_value=0, step=1, value=3)
        with col2:
            reps = st.number_input("Reps", min_value=0, step=1, value=10)
            weight = st.number_input("Weight (kg)", min_value=0.0, step=0.5, value=20.0)
            rpe = st.slider("RPE", min_value=1, max_value=10, value=7)
        notes = st.text_input("Notes (optional)")
        submitted = st.form_submit_button("Save Workout", use_container_width=True)

        if submitted:
            if not exercise:
                st.error("Please select or enter an exercise.")
            else:
                result = WA.log_workout_entry(
                    log_date, muscle_choice, exercise, sets, reps, weight, rpe, notes,
                    workout_df=workout_df,
                )
                volume, est_1rm = result["volume"], result["est_1rm"]
                broken_prs, overload_status = result["broken_prs"], result["overload_status"]
                xp_result, pr_xp = result["xp_result"], result["pr_xp"]

                st.success(f"Workout saved. Volume: {volume} | Est. 1RM: {est_1rm} kg (+100 XP)")

                if broken_prs:
                    st.balloons()
                    st.success(f"🏆 NEW PR! Broke: {', '.join(broken_prs)} (+200 XP)")

                st.info(f"Progressive Overload: **{overload_status}**")

                if xp_result["leveled_up"] or pr_xp["leveled_up"]:
                    st.success(f"🎉 LEVEL UP! You are now Level {RPG.load_rpg_state()['level']}")

                unlocked = WA.post_log_achievements_check()
                for ach in unlocked:
                    st.success(f"🏅 Achievement Unlocked: {ach['name']}!")

                st.rerun()

st.divider()

# ----------------------------------------------------------------------
# PR Tracker
# ----------------------------------------------------------------------
workout_df = DM.load_workout_log()

if not workout_df.empty:
    st.markdown("#### PR Tracker")
    exercise_options = sorted(workout_df["exercise"].dropna().unique().tolist())
    pr_exercise = st.selectbox("View PRs for", exercise_options, key="pr_exercise_select")
    prs = calc.get_prs_for_exercise(workout_df, pr_exercise)
    p1, p2, p3, p4 = st.columns(4)
    p1.metric("Highest Weight", f"{prs['weight']:.1f} kg")
    p2.metric("Highest Reps", f"{prs['reps']:.0f}")
    p3.metric("Highest Volume", f"{prs['volume']:.0f}")
    p4.metric("Highest Est. 1RM", f"{prs['est_1rm']:.1f} kg")

    st.divider()

    # ----------------------------------------------------------------------
    # History
    # ----------------------------------------------------------------------
    st.markdown("#### Workout History")
    history = workout_df.copy()
    history["date"] = pd.to_datetime(history["date"], errors="coerce")
    history = history.sort_values("date", ascending=False)
    display_cols = ["date", "muscle_group", "exercise", "sets", "reps", "weight", "rpe", "volume", "est_1rm", "is_pr", "notes"]
    st.dataframe(history[display_cols], use_container_width=True, hide_index=True)

    st.divider()

    # ----------------------------------------------------------------------
    # Charts
    # ----------------------------------------------------------------------
    chart1, chart2 = st.columns(2)
    with chart1:
        st.markdown("#### Volume by Muscle Group")
        vol_by_group = calc.volume_by_muscle_group(workout_df)
        fig = px.bar(vol_by_group, x="muscle_group", y="volume")
        fig.update_layout(template="plotly_dark", height=320, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig, use_container_width=True)

    with chart2:
        st.markdown("#### Volume Over Time")
        v_over_time = workout_df.copy()
        v_over_time["date"] = pd.to_datetime(v_over_time["date"], errors="coerce")
        daily_vol = v_over_time.groupby(v_over_time["date"].dt.date)["volume"].sum().reset_index()
        daily_vol.columns = ["date", "volume"]
        fig = px.line(daily_vol, x="date", y="volume", markers=True)
        fig.update_layout(template="plotly_dark", height=320, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig, use_container_width=True)

    chart3, chart4 = st.columns(2)
    with chart3:
        st.markdown("#### Weekly Volume Trend")
        weekly = calc.volume_trend(workout_df, freq="W")
        fig = px.bar(weekly, x="period", y="volume")
        fig.update_layout(template="plotly_dark", height=300, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig, use_container_width=True)

    with chart4:
        st.markdown("#### Monthly Volume Trend")
        monthly = calc.volume_trend(workout_df, freq="M")
        fig = px.bar(monthly, x="period", y="volume")
        fig.update_layout(template="plotly_dark", height=300, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No workouts logged yet. Use the form above to log your first one.")

bottom_tab_bar(active="workout")
