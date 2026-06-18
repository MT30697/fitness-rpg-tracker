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


def _build_workout_row(log_date, muscle_group: str, exercise: str, sets, reps, weight, rpe, notes: str,
                        workout_df: pd.DataFrame) -> tuple[dict, list, str]:
    """Pure computation, no I/O: volume/est_1RM, PR detection, overload
    status. Returns (row_dict, broken_prs, overload_status)."""
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
    return row, broken_prs, overload_status


def log_workout_entry(log_date, muscle_group: str, exercise: str, sets, reps, weight, rpe, notes: str = "",
                       workout_df: pd.DataFrame | None = None) -> dict:
    """Logs ONE exercise entry immediately (its own write + its own XP
    award). Fine for a single manual log. For logging several exercises
    back to back (e.g. a whole template), use log_workout_entries_batch
    instead — calling this in a loop means one Google Sheets write per
    exercise, which can hit API rate limits."""
    if workout_df is None:
        workout_df = DM.load_workout_log()

    row, broken_prs, overload_status = _build_workout_row(
        log_date, muscle_group, exercise, sets, reps, weight, rpe, notes, workout_df,
    )
    DM.append_csv_row(C.WORKOUT_LOG_FILE, row, C.WORKOUT_LOG_COLUMNS)

    xp_result = RPG.award_xp("workout_logged")
    pr_xp = {"leveled_up": False}
    if broken_prs:
        pr_xp = RPG.award_xp("new_pr")

    return {
        "volume": row["volume"],
        "est_1rm": row["est_1rm"],
        "broken_prs": broken_prs,
        "overload_status": overload_status,
        "xp_result": xp_result,
        "pr_xp": pr_xp,
    }


def log_workout_entries_batch(entries: list[tuple], workout_df: pd.DataFrame | None = None) -> dict:
    """Logs several exercise entries in ONE write + ONE XP award, instead
    of one of each per exercise. Use for template quick-logging.

    entries: list of (log_date, muscle_group, exercise, sets, reps, weight, rpe, notes) tuples.
    Returns {"per_exercise": [{"exercise", "broken_prs", "overload_status", "row"}...],
             "xp_result": {...}}."""
    if workout_df is None:
        workout_df = DM.load_workout_log()

    rows = []
    per_exercise = []
    xp_reasons = []
    for entry in entries:
        row, broken_prs, overload_status = _build_workout_row(*entry, workout_df=workout_df)
        rows.append(row)
        xp_reasons.append("workout_logged")
        if broken_prs:
            xp_reasons.append("new_pr")
        per_exercise.append({
            "exercise": entry[2], "broken_prs": broken_prs,
            "overload_status": overload_status, "row": row,
        })

    if rows:
        DM.append_csv_rows(C.WORKOUT_LOG_FILE, rows, C.WORKOUT_LOG_COLUMNS)

    xp_result = RPG.award_xp_batch(xp_reasons) if xp_reasons else {"leveled_up": False, "amount_awarded": 0}

    return {"per_exercise": per_exercise, "xp_result": xp_result}


def post_log_achievements_check() -> list[dict]:
    """Run once after one or more log calls (once per batch, not once per
    exercise) — checks streak/PR/weekly achievements against the
    freshest saved data and returns any newly unlocked ones."""
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
