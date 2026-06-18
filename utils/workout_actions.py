"""
Shared workout-logging logic used by both pages/workout_log.py (single
manual entry) and pages/workout_templates.py (batch quick-log from a
saved template), so the volume/PR/XP/achievement rules live in exactly
one place.
"""
from __future__ import annotations

from datetime import date

import pandas as pd

from utils import calculations as calc
from utils import constants as C
from utils import data_manager as DM
from utils import rpg_engine as RPG


def log_workout_entry(log_date, muscle_group: str, exercise: str, sets, reps, weight, rpe, notes: str = "",
                       workout_df: pd.DataFrame | None = None) -> dict:
    """Logs one exercise entry: computes volume/est_1RM, detects PRs and
    progressive-overload status, saves the row, and awards XP. Returns a
    result dict the caller can use to render success/PR messages.

    workout_df: pass an already-loaded DataFrame to avoid re-reading
    storage when logging several exercises back to back (e.g. a template
    batch) — each call still re-reads internally if not provided."""
    if workout_df is None:
        workout_df = DM.load_workout_log()

    volume = calc.calc_volume(sets, reps, weight)
    est_1rm = calc.calc_est_1rm(weight, reps)

    prior_prs = calc.get_prs_for_exercise(workout_df, exercise)
    overload_status = calc.detect_progressive_overload(workout_df, exercise, volume)
    broken_prs = calc.check_new_pr(prior_prs, weight, reps, volume, est_1rm)

    row = {
        "log_id": DM.generate_id(),
        "date": log_date.isoformat() if hasattr(log_date, "isoformat") else str(log_date),
        "muscle_group": muscle_group,
        "exercise": exercise,
        "sets": sets,
        "reps": reps,
        "weight": weight,
        "rpe": rpe,
        "notes": (notes or "").strip(),
        "volume": volume,
        "est_1rm": est_1rm,
        "is_pr": bool(broken_prs),
        "created_at": DM.now_iso(),
    }
    DM.append_csv_row(C.WORKOUT_LOG_FILE, row, C.WORKOUT_LOG_COLUMNS)

    xp_result = RPG.award_xp("workout_logged")
    pr_xp = {"leveled_up": False}
    if broken_prs:
        pr_xp = RPG.award_xp("new_pr")

    return {
        "volume": volume,
        "est_1rm": est_1rm,
        "broken_prs": broken_prs,
        "overload_status": overload_status,
        "xp_result": xp_result,
        "pr_xp": pr_xp,
    }


def post_log_achievements_check() -> list[dict]:
    """Run once after one or more log_workout_entry() calls (once per
    batch, not once per exercise) — checks streak/PR/weekly achievements
    against the freshest saved data and returns any newly unlocked ones."""
    refreshed = DM.load_workout_log()
    refreshed["date_only"] = pd.to_datetime(refreshed["date"], errors="coerce").dt.date
    streak = calc.compute_streak(refreshed["date_only"].tolist())
    total_prs = int(refreshed["is_pr"].astype(str).str.lower().eq("true").sum()) if "is_pr" in refreshed else 0
    workouts_this_week = refreshed[
        refreshed["date_only"] >= (date.today() - pd.Timedelta(days=date.today().weekday()))
    ]["date_only"].nunique()

    unlocked = RPG.check_achievements({
        "total_workouts": refreshed["date_only"].nunique(),
        "workout_streak": streak,
        "total_prs": total_prs,
    })
    RPG.maybe_award_weekly_goal(workouts_this_week)
    return unlocked
