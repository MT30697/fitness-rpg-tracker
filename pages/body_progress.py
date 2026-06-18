"""Body Progress - weight, waist, body fat check-ins and goal prediction."""
from __future__ import annotations

from datetime import date

import pandas as pd
import plotly.express as px
import streamlit as st

from components.ui import bottom_tab_bar, page_header
from utils import calculations as calc
from utils import constants as C
from utils import data_manager as DM
from utils import rpg_engine as RPG

page_header("Body Progress", "📈", "Check in, track trends, and see your goal date.")

settings = DM.load_settings()
body_df = DM.load_body_progress()

# ----------------------------------------------------------------------
# Log a check-in
# ----------------------------------------------------------------------
with st.expander("➕ Log Body Check-in", expanded=True):
    with st.form("body_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            log_date = st.date_input("Date", value=date.today())
            weight = st.number_input("Weight (kg)", min_value=0.0, step=0.1, value=float(settings.get("current_weight_kg") or 0))
        with col2:
            waist = st.number_input("Waist (cm, optional)", min_value=0.0, step=0.5, value=0.0)
            body_fat = st.number_input("Body Fat % (optional)", min_value=0.0, step=0.1, value=0.0)
        photo = st.file_uploader("Progress Photo (optional)", type=["png", "jpg", "jpeg"])
        notes = st.text_input("Notes (optional)")
        submitted = st.form_submit_button("Save Check-in", use_container_width=True)

        if submitted:
            photo_path = ""
            if photo is not None:
                C.BODY_PHOTOS_DIR.mkdir(parents=True, exist_ok=True)
                ext = photo.name.split(".")[-1]
                filename = f"{log_date.isoformat()}_{DM.generate_id()}.{ext}"
                dest = C.BODY_PHOTOS_DIR / filename
                with open(dest, "wb") as f:
                    f.write(photo.getbuffer())
                photo_path = str(dest)

            row = {
                "log_id": DM.generate_id(),
                "date": log_date.isoformat(),
                "weight": weight,
                "waist": waist if waist else None,
                "body_fat": body_fat if body_fat else None,
                "photo": photo_path,
                "notes": notes.strip(),
                "created_at": DM.now_iso(),
            }
            DM.append_csv_row(C.BODY_PROGRESS_FILE, row, C.BODY_PROGRESS_COLUMNS)

            # keep settings in sync with the latest weight/waist for other pages
            settings["current_weight_kg"] = weight
            if waist:
                settings["waist_cm"] = waist
            DM.save_settings(settings)

            xp_result = RPG.award_xp("body_checkin")
            st.success("Check-in saved. (+20 XP)")
            if xp_result["leveled_up"]:
                st.success(f"🎉 LEVEL UP! You are now Level {RPG.load_rpg_state()['level']}")

            refreshed = DM.load_body_progress()
            refreshed_sorted = refreshed.copy()
            refreshed_sorted["date"] = pd.to_datetime(refreshed_sorted["date"], errors="coerce")
            refreshed_sorted = refreshed_sorted.dropna(subset=["date"]).sort_values("date")
            starting_weight = float(refreshed_sorted.iloc[0]["weight"]) if not refreshed_sorted.empty else weight

            unlocked = RPG.check_achievements({
                "total_body_checkins": len(refreshed),
                "starting_weight": starting_weight,
                "current_weight": weight,
                "goal_weight": settings.get("goal_weight_kg"),
            })
            for ach in unlocked:
                st.success(f"🏅 Achievement Unlocked: {ach['name']}!")

            st.rerun()

st.divider()

body_df = DM.load_body_progress()

if body_df.empty:
    st.info("No body check-ins yet. Use the form above to log your first one.")
else:
    bdf = body_df.copy()
    bdf["date"] = pd.to_datetime(bdf["date"], errors="coerce")
    bdf = bdf.dropna(subset=["date"]).sort_values("date")

    starting_weight = float(bdf.iloc[0]["weight"])
    current_weight = float(bdf.iloc[-1]["weight"])
    goal_weight = settings.get("goal_weight_kg") or current_weight

    weight_lost = round(starting_weight - current_weight, 1)
    weight_remaining = round(current_weight - goal_weight, 1)

    c1, c2, c3 = st.columns(3)
    c1.metric("Weight Lost", f"{weight_lost:.1f} kg")
    c2.metric("Weight Remaining", f"{abs(weight_remaining):.1f} kg")
    c3.metric("Current Weight", f"{current_weight:.1f} kg")

    prediction = calc.goal_prediction(bdf, goal_weight)
    st.markdown("#### Goal Prediction")
    if prediction["predicted_date"]:
        st.success(
            f"At your recent rate ({prediction['rate_per_day']:.3f} kg/day over the last 14 days), "
            f"you're projected to reach your goal weight around **{prediction['predicted_date']}** "
            f"(~{prediction['days_remaining']} days)."
        )
    else:
        st.info(prediction["message"])

    st.divider()
    chart1, chart2, chart3 = st.columns(3)
    with chart1:
        st.markdown("#### Weight Trend")
        fig = px.line(bdf, x="date", y="weight", markers=True)
        fig.add_hline(y=goal_weight, line_dash="dot", line_color="#ffffff", annotation_text="Goal")
        fig.update_layout(template="plotly_dark", height=300, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig, use_container_width=True)

    with chart2:
        st.markdown("#### Waist Trend")
        waist_data = bdf.dropna(subset=["waist"])
        if not waist_data.empty:
            fig = px.line(waist_data, x="date", y="waist", markers=True)
            fig.update_layout(template="plotly_dark", height=300, margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No waist measurements logged yet.")

    with chart3:
        st.markdown("#### Body Fat Trend")
        bf_data = bdf.dropna(subset=["body_fat"])
        if not bf_data.empty:
            fig = px.line(bf_data, x="date", y="body_fat", markers=True)
            fig.update_layout(template="plotly_dark", height=300, margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No body fat measurements logged yet.")

    st.divider()
    st.markdown("#### Photo Timeline")
    photo_rows = bdf[bdf["photo"].notna() & (bdf["photo"] != "")]
    if photo_rows.empty:
        st.info("No progress photos uploaded yet.")
    else:
        cols = st.columns(4)
        for i, (_, row) in enumerate(photo_rows.iterrows()):
            with cols[i % 4]:
                try:
                    st.image(row["photo"], caption=row["date"].date().isoformat(), use_container_width=True)
                except Exception:
                    st.caption(f"Photo missing for {row['date'].date().isoformat()}")

    st.divider()
    st.markdown("#### Check-in History")
    st.dataframe(
        bdf.sort_values("date", ascending=False)[["date", "weight", "waist", "body_fat", "notes"]],
        use_container_width=True, hide_index=True,
    )

bottom_tab_bar(active="more")
