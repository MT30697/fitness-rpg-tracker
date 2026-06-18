"""Nutrition - log meals and track macro targets."""
from __future__ import annotations

from datetime import date

import pandas as pd
import plotly.express as px
import streamlit as st

from components.ui import page_header, progress_bar, render_badges, status_to_style
from utils import calculations as calc
from utils import constants as C
from utils import data_manager as DM
from utils import rpg_engine as RPG

page_header("Nutrition", "🍽️", "Track meals, macros and calories against your targets.")

settings = DM.load_settings()
targets = settings.get("nutrition_targets", C.DEFAULT_SETTINGS["nutrition_targets"])
nutrition_df = DM.load_nutrition_log()

# ----------------------------------------------------------------------
# Log entry
# ----------------------------------------------------------------------
with st.expander("➕ Log Food Entry", expanded=True):
    with st.form("nutrition_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            log_date = st.date_input("Date", value=date.today())
            meal_type = st.selectbox("Meal Type", C.MEAL_TYPES)
            food_name = st.text_input("Food Name")
        with col2:
            protein = st.number_input("Protein (g)", min_value=0.0, step=1.0, value=0.0)
            carbs = st.number_input("Carbs (g)", min_value=0.0, step=1.0, value=0.0)
            fat = st.number_input("Fat (g)", min_value=0.0, step=1.0, value=0.0)
        calories = st.number_input(
            "Calories", min_value=0.0, step=10.0,
            value=float(round(protein * 4 + carbs * 4 + fat * 9)),
            help="Defaults to a macro-based estimate; override if you know the real value.",
        )
        notes = st.text_input("Notes (optional)")
        submitted = st.form_submit_button("Save Food Entry", use_container_width=True)

        if submitted:
            if not food_name.strip():
                st.error("Food name is required.")
            else:
                row = {
                    "log_id": DM.generate_id(),
                    "date": log_date.isoformat(),
                    "meal_type": meal_type,
                    "food_name": food_name.strip(),
                    "protein": protein,
                    "carbs": carbs,
                    "fat": fat,
                    "calories": calories,
                    "notes": notes.strip(),
                    "created_at": DM.now_iso(),
                }
                DM.append_csv_row(C.NUTRITION_LOG_FILE, row, C.NUTRITION_LOG_COLUMNS)
                st.success("Food entry saved.")

                refreshed = DM.load_nutrition_log()
                today_macros = calc.daily_macro_summary(refreshed, log_date)
                status = calc.macro_status(today_macros, targets)
                if status["protein"] == "Protein Goal Met":
                    xp_result = RPG.award_xp("protein_goal_met")
                    st.success("🍗 Protein goal met today! (+50 XP)")
                    if xp_result["leveled_up"]:
                        st.success(f"🎉 LEVEL UP! You are now Level {RPG.load_rpg_state()['level']}")

                st.rerun()

st.divider()

# ----------------------------------------------------------------------
# Daily summary
# ----------------------------------------------------------------------
nutrition_df = DM.load_nutrition_log()
today = date.today()
selected_day = st.date_input("View summary for", value=today, key="nutrition_summary_date")

day_summary = calc.daily_macro_summary(nutrition_df, selected_day)
status = calc.macro_status(day_summary, targets)

st.markdown("#### Daily Macro Summary")
m1, m2, m3, m4 = st.columns(4)
m1.metric("Protein", f"{day_summary['protein']:.0f} g", f"target {targets.get('protein')}g")
m2.metric("Carbs", f"{day_summary['carbs']:.0f} g", f"target {targets.get('carbs')}g")
m3.metric("Fat", f"{day_summary['fat']:.0f} g", f"target {targets.get('fat')}g")
m4.metric("Calories", f"{day_summary['calories']:.0f}", f"target {targets.get('calories')}")

st.write("")
st.markdown("#### Macro Progress")
progress_bar("Protein", day_summary["protein"], targets.get("protein", 1), "g")
progress_bar("Carbs", day_summary["carbs"], targets.get("carbs", 1), "g")
progress_bar("Fat", day_summary["fat"], targets.get("fat", 1), "g")
progress_bar("Calories", day_summary["calories"], targets.get("calories", 1), "")

st.write("")
render_badges([(status["protein"], status_to_style(status["protein"])), (status["calories"], status_to_style(status["calories"]))])

st.divider()

# ----------------------------------------------------------------------
# History & charts
# ----------------------------------------------------------------------
if nutrition_df.empty:
    st.info("No food logged yet. Use the form above to log your first entry.")
else:
    st.markdown("#### Food Log History")
    history = nutrition_df.copy()
    history["date"] = pd.to_datetime(history["date"], errors="coerce")
    history = history.sort_values("date", ascending=False)
    st.dataframe(
        history[["date", "meal_type", "food_name", "protein", "carbs", "fat", "calories", "notes"]],
        use_container_width=True, hide_index=True,
    )

    st.divider()
    chart1, chart2 = st.columns(2)
    with chart1:
        st.markdown("#### Calories Over Time")
        daily_cal = history.groupby(history["date"].dt.date)["calories"].sum().reset_index()
        daily_cal.columns = ["date", "calories"]
        fig = px.bar(daily_cal, x="date", y="calories")
        fig.add_hline(y=targets.get("calories", 0), line_dash="dot", line_color="#ffffff", annotation_text="Target")
        fig.update_layout(template="plotly_dark", height=320, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig, use_container_width=True)

    with chart2:
        st.markdown("#### Macro Split (selected day)")
        macro_split = pd.DataFrame({
            "macro": ["Protein", "Carbs", "Fat"],
            "grams": [day_summary["protein"], day_summary["carbs"], day_summary["fat"]],
        })
        fig = px.pie(macro_split, names="macro", values="grams", hole=0.45)
        fig.update_layout(template="plotly_dark", height=320, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig, use_container_width=True)
