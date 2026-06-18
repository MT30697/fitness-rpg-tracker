"""Dashboard - home page."""
from __future__ import annotations

from datetime import date, timedelta

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from components.ui import level_ring, metric_card, page_header, progress_bar, render_badges, status_to_style
from utils import calculations as calc
from utils import constants as C
from utils import data_manager as DM
from utils import rpg_engine as RPG

page_header("Dashboard", "🏠", "Your daily command center.")

settings = DM.load_settings()
workout_df = DM.load_workout_log()
cardio_df = DM.load_cardio_log()
nutrition_df = DM.load_nutrition_log()
body_df = DM.load_body_progress()

today = date.today()
week_start = today - timedelta(days=today.weekday())

# ----------------------------------------------------------------------
# Derived stats
# ----------------------------------------------------------------------
current_weight = settings.get("current_weight_kg")
if not body_df.empty:
    body_sorted = body_df.copy()
    body_sorted["date"] = pd.to_datetime(body_sorted["date"], errors="coerce")
    body_sorted = body_sorted.dropna(subset=["date"]).sort_values("date")
    if not body_sorted.empty:
        current_weight = float(body_sorted.iloc[-1]["weight"])
        latest_waist = body_sorted.iloc[-1]["waist"]
    else:
        latest_waist = settings.get("waist_cm")
else:
    latest_waist = settings.get("waist_cm")

goal_weight = settings.get("goal_weight_kg") or 0
weight_remaining = round((current_weight or 0) - goal_weight, 1)

workouts_this_week = 0
if not workout_df.empty:
    wdf = workout_df.copy()
    wdf["date"] = pd.to_datetime(wdf["date"], errors="coerce").dt.date
    workouts_this_week = wdf[wdf["date"] >= week_start]["date"].nunique()

cardio_minutes_week = 0.0
if not cardio_df.empty:
    cdf = cardio_df.copy()
    cdf["date"] = pd.to_datetime(cdf["date"], errors="coerce").dt.date
    cardio_minutes_week = float(cdf[cdf["date"] >= week_start]["duration"].sum() or 0)

macros_today = calc.daily_macro_summary(nutrition_df, today)
targets = settings.get("nutrition_targets", C.DEFAULT_SETTINGS["nutrition_targets"])
macro_stat = calc.macro_status(macros_today, targets)

rpg_state = RPG.load_rpg_state()
level_info = RPG.get_level_info(rpg_state.get("xp", 0))

workout_logged_today = not workout_df.empty and (
    pd.to_datetime(workout_df["date"], errors="coerce").dt.date == today
).any()
cardio_logged_today = not cardio_df.empty and (
    pd.to_datetime(cardio_df["date"], errors="coerce").dt.date == today
).any()
body_checkin_today = not body_df.empty and (
    pd.to_datetime(body_df["date"], errors="coerce").dt.date == today
).any()

daily_score = calc.compute_daily_score(
    workout_logged=workout_logged_today,
    cardio_logged=cardio_logged_today,
    protein_met=macro_stat["protein"] == "Protein Goal Met",
    calories_on_target=macro_stat["calories"] == "Calories On Target",
    body_checkin=body_checkin_today,
)

# ----------------------------------------------------------------------
# Top metric row
# ----------------------------------------------------------------------
c1, c2, c3, c4 = st.columns(4)
with c1:
    metric_card("Current Weight", f"{current_weight:.1f} kg" if current_weight else "—", module="body")
with c2:
    metric_card("Goal Weight", f"{goal_weight:.1f} kg", module="body")
with c3:
    sign = "to lose" if weight_remaining > 0 else "to gain" if weight_remaining < 0 else "at goal"
    metric_card("Weight Remaining", f"{abs(weight_remaining):.1f} kg", sign, module="body")
with c4:
    metric_card("Latest Waist", f"{latest_waist:.1f} cm" if latest_waist else "—", module="body")

c5, c6, c7, c8 = st.columns(4)
with c5:
    metric_card("Workouts This Week", str(workouts_this_week), module="workout")
with c6:
    metric_card("Cardio Minutes This Week", f"{cardio_minutes_week:.0f} min", module="cardio")
with c7:
    metric_card("Protein Today", f"{macros_today['protein']:.0f} g", f"target {targets.get('protein')}g", module="nutrition")
with c8:
    metric_card("Calories Today", f"{macros_today['calories']:.0f}", f"target {targets.get('calories')}", module="nutrition")

c9, c10 = st.columns([1, 1])
with c9:
    st.markdown('<div class="rpg-card"><div class="rpg-card-tag">LEVEL</div>', unsafe_allow_html=True)
    level_ring(level_info["level"], level_info["xp_into_level"], C.XP_PER_LEVEL, level_info["xp"])
    st.markdown("</div>", unsafe_allow_html=True)
with c10:
    metric_card("Daily Score", f"{daily_score} / 100", "today", module="score")

st.write("")

# ----------------------------------------------------------------------
# Today's status row
# ----------------------------------------------------------------------
left, right = st.columns([2, 1])
with left:
    st.markdown("#### Today's Status")
    badges = [
        ("Workout Logged" if workout_logged_today else "No Workout Yet",
         "success" if workout_logged_today else "warning"),
        ("Cardio Logged" if cardio_logged_today else "No Cardio Yet",
         "success" if cardio_logged_today else "warning"),
        (macro_stat["protein"], status_to_style(macro_stat["protein"])),
        (macro_stat["calories"], status_to_style(macro_stat["calories"])),
        ("Body Check-in Done" if body_checkin_today else "No Check-in Yet",
         "success" if body_checkin_today else "warning"),
    ]
    render_badges(badges)

with right:
    st.markdown("#### Today's Reminder")
    weekday_name = today.strftime("%A")
    is_workout_day = weekday_name in settings.get("workout_days", [])
    st.markdown(f"🏃 Cardio reminder: **{settings.get('cardio_reminder_time', '06:00')}**")
    if is_workout_day:
        st.markdown(f"🏋️ Gym reminder: **{settings.get('gym_reminder_time', '14:00')}** (workout day)")
    else:
        st.markdown("🛌 No scheduled workout today")

st.write("")
st.markdown("#### Macro Progress")
m1, m2, m3, m4 = st.columns(4)
with m1:
    progress_bar("Protein", macros_today["protein"], targets.get("protein", 1), "g")
with m2:
    progress_bar("Carbs", macros_today["carbs"], targets.get("carbs", 1), "g")
with m3:
    progress_bar("Fat", macros_today["fat"], targets.get("fat", 1), "g")
with m4:
    progress_bar("Calories", macros_today["calories"], targets.get("calories", 1), "")

st.divider()

# ----------------------------------------------------------------------
# Charts
# ----------------------------------------------------------------------
chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    st.markdown("#### Weight Trend")
    if not body_df.empty:
        wb = body_df.copy()
        wb["date"] = pd.to_datetime(wb["date"], errors="coerce")
        wb = wb.dropna(subset=["date"]).sort_values("date")
        if not wb.empty:
            fig = px.line(wb, x="date", y="weight", markers=True)
            fig.add_hline(y=goal_weight, line_dash="dot", line_color="#ffffff",
                           annotation_text="Goal", annotation_position="bottom right")
            fig.update_layout(template="plotly_dark", height=320, margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Log your weight in Body Progress to see this chart.")
    else:
        st.info("Log your weight in Body Progress to see this chart.")

with chart_col2:
    st.markdown("#### Workout Volume (Weekly)")
    trend = calc.volume_trend(workout_df, freq="W")
    if not trend.empty:
        fig = px.bar(trend, x="period", y="volume")
        fig.update_layout(template="plotly_dark", height=320, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Log workouts to see your volume trend.")

chart_col3, chart_col4 = st.columns(2)
with chart_col3:
    st.markdown("#### Cardio Minutes (Daily, last 14 days)")
    if not cardio_df.empty:
        cd = cardio_df.copy()
        cd["date"] = pd.to_datetime(cd["date"], errors="coerce")
        cd = cd.dropna(subset=["date"])
        cutoff = pd.Timestamp(today - timedelta(days=14))
        cd = cd[cd["date"] >= cutoff]
        if not cd.empty:
            daily = cd.groupby(cd["date"].dt.date)["duration"].sum().reset_index()
            daily.columns = ["date", "duration"]
            fig = px.bar(daily, x="date", y="duration")
            fig.update_layout(template="plotly_dark", height=320, margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No cardio logged in the last 14 days.")
    else:
        st.info("Log a cardio session to see this chart.")

with chart_col4:
    st.markdown("#### Weekly Activity Heatmap")
    days_back = 84  # 12 weeks
    all_dates = []
    for df, col in [(workout_df, "date"), (cardio_df, "date"), (nutrition_df, "date"), (body_df, "date")]:
        if not df.empty:
            all_dates.extend(pd.to_datetime(df[col], errors="coerce").dropna().dt.date.tolist())

    date_range = [today - timedelta(days=i) for i in range(days_back)][::-1]
    counts = {d: 0 for d in date_range}
    for d in all_dates:
        if d in counts:
            counts[d] += 1

    heat_df = pd.DataFrame({"date": date_range, "count": [counts[d] for d in date_range]})
    heat_df["week"] = heat_df["date"].apply(lambda d: (d - date_range[0]).days // 7)
    heat_df["weekday"] = heat_df["date"].apply(lambda d: d.weekday())

    pivot = heat_df.pivot(index="weekday", columns="week", values="count").fillna(0)
    fig = go.Figure(
        data=go.Heatmap(
            z=pivot.values,
            x=[f"W{w}" for w in pivot.columns],
            y=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
            colorscale=[[0, "#0a0a0a"], [0.5, "#5a5a5a"], [1, "#ffffff"]],
            showscale=False,
        )
    )
    fig.update_layout(template="plotly_dark", height=320, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig, use_container_width=True)
