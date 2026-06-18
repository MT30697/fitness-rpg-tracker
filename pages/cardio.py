"""Cardio - log cardio sessions and track activity over time."""
from __future__ import annotations

from datetime import date, timedelta

import pandas as pd
import plotly.express as px
import streamlit as st

from components.ui import page_header
from utils import calculations as calc
from utils import constants as C
from utils import data_manager as DM
from utils import rpg_engine as RPG

page_header("Cardio", "🏃", "Log walking, running, cycling and more.")

cardio_df = DM.load_cardio_log()

# ----------------------------------------------------------------------
# Log entry
# ----------------------------------------------------------------------
with st.expander("➕ Log Cardio Session", expanded=True):
    with st.form("cardio_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            log_date = st.date_input("Date", value=date.today())
            cardio_type = st.selectbox("Type", C.CARDIO_TYPES)
            duration = st.number_input("Duration (minutes)", min_value=0.0, step=1.0, value=30.0)
            distance = st.number_input("Distance (km)", min_value=0.0, step=0.1, value=0.0)
        with col2:
            speed = st.number_input("Speed (km/h)", min_value=0.0, step=0.1, value=0.0)
            incline = st.number_input("Incline (%)", min_value=0.0, step=0.5, value=0.0)
            steps = st.number_input("Steps", min_value=0, step=100, value=0)
            calories = st.number_input("Calories Burned", min_value=0.0, step=10.0, value=0.0)
        notes = st.text_input("Notes (optional)")
        submitted = st.form_submit_button("Save Cardio Session", use_container_width=True)

        if submitted:
            row = {
                "log_id": DM.generate_id(),
                "date": log_date.isoformat(),
                "type": cardio_type,
                "duration": duration,
                "distance": distance,
                "speed": speed,
                "incline": incline,
                "steps": steps,
                "calories_burned": calories,
                "notes": notes.strip(),
                "created_at": DM.now_iso(),
            }
            DM.append_csv_row(C.CARDIO_LOG_FILE, row, C.CARDIO_LOG_COLUMNS)
            xp_result = RPG.award_xp("cardio_logged")
            st.success(f"Cardio session saved. (+50 XP)")
            if xp_result["leveled_up"]:
                st.success(f"🎉 LEVEL UP! You are now Level {RPG.load_rpg_state()['level']}")

            refreshed = DM.load_cardio_log()
            unlocked = RPG.check_achievements({
                "total_cardio_sessions": len(refreshed),
                "max_steps_single_day": refreshed["steps"].max() if "steps" in refreshed and not refreshed.empty else 0,
            })
            for ach in unlocked:
                st.success(f"🏅 Achievement Unlocked: {ach['name']}!")

            st.rerun()

st.divider()

cardio_df = DM.load_cardio_log()

if cardio_df.empty:
    st.info("No cardio sessions logged yet. Use the form above to log your first one.")
else:
    cdf = cardio_df.copy()
    cdf["date"] = pd.to_datetime(cdf["date"], errors="coerce")
    today = date.today()

    daily_today = cdf[cdf["date"].dt.date == today]
    week_start = today - timedelta(days=today.weekday())
    weekly = cdf[cdf["date"].dt.date >= week_start]
    month_start = today.replace(day=1)
    monthly = cdf[cdf["date"].dt.date >= month_start]

    c1, c2, c3 = st.columns(3)
    c1.metric("Daily Cardio (today)", f"{daily_today['duration'].sum():.0f} min")
    c2.metric("Weekly Cardio", f"{weekly['duration'].sum():.0f} min")
    c3.metric("Monthly Cardio", f"{monthly['duration'].sum():.0f} min")

    s1, s2, s3 = st.columns(3)
    s1.metric("Steps Today", f"{daily_today['steps'].sum():.0f}")
    s2.metric("Steps This Week", f"{weekly['steps'].sum():.0f}")
    s3.metric("Calories Burned Today", f"{daily_today['calories_burned'].sum():.0f}")

    st.divider()
    st.markdown("#### Cardio History")
    history = cdf.sort_values("date", ascending=False)
    st.dataframe(
        history[["date", "type", "duration", "distance", "speed", "incline", "steps", "calories_burned", "notes"]],
        use_container_width=True, hide_index=True,
    )

    st.divider()
    chart1, chart2 = st.columns(2)
    with chart1:
        st.markdown("#### Duration Over Time")
        daily_chart = cdf.groupby(cdf["date"].dt.date)["duration"].sum().reset_index()
        daily_chart.columns = ["date", "duration"]
        fig = px.bar(daily_chart, x="date", y="duration")
        fig.update_layout(template="plotly_dark", height=320, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig, use_container_width=True)

    with chart2:
        st.markdown("#### Step Tracking")
        steps_chart = cdf.groupby(cdf["date"].dt.date)["steps"].sum().reset_index()
        steps_chart.columns = ["date", "steps"]
        fig = px.line(steps_chart, x="date", y="steps", markers=True)
        fig.add_hline(y=10000, line_dash="dot", line_color="#ffffff", annotation_text="10K Goal")
        fig.update_layout(template="plotly_dark", height=320, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("#### Cardio Type Breakdown")
    by_type = cdf.groupby("type")["duration"].sum().reset_index()
    fig = px.pie(by_type, names="type", values="duration", hole=0.45)
    fig.update_layout(template="plotly_dark", height=320, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig, use_container_width=True)
