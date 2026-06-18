"""
Pure calculation helpers - no Streamlit, no I/O. Easy to unit test.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Optional

import pandas as pd

from utils import constants as C


# ----------------------------------------------------------------------
# Workout math
# ----------------------------------------------------------------------
def calc_volume(sets: float, reps: float, weight: float) -> float:
    sets, reps, weight = float(sets or 0), float(reps or 0), float(weight or 0)
    return round(sets * reps * weight, 2)


def calc_est_1rm(weight: float, reps: float) -> float:
    weight, reps = float(weight or 0), float(reps or 0)
    return round(weight * (1 + reps / 30), 2)


def get_prs_for_exercise(workout_df: pd.DataFrame, exercise: str) -> dict:
    """Return current PRs (max weight, reps, volume, est_1rm) for an exercise,
    BEFORE the row currently being evaluated. Empty/missing data -> zeros."""
    if workout_df is None or workout_df.empty:
        return {"weight": 0.0, "reps": 0.0, "volume": 0.0, "est_1rm": 0.0}
    subset = workout_df[workout_df["exercise"] == exercise]
    if subset.empty:
        return {"weight": 0.0, "reps": 0.0, "volume": 0.0, "est_1rm": 0.0}
    return {
        "weight": float(subset["weight"].max() or 0),
        "reps": float(subset["reps"].max() or 0),
        "volume": float(subset["volume"].max() or 0),
        "est_1rm": float(subset["est_1rm"].max() or 0),
    }


def check_new_pr(prior_prs: dict, weight: float, reps: float, volume: float, est_1rm: float) -> list[str]:
    """Compare a new set against prior PRs. Returns list of PR types broken,
    e.g. ['weight', 'est_1rm']. Empty list if no PR."""
    broken = []
    if weight > prior_prs.get("weight", 0):
        broken.append("weight")
    if reps > prior_prs.get("reps", 0):
        broken.append("reps")
    if volume > prior_prs.get("volume", 0):
        broken.append("volume")
    if est_1rm > prior_prs.get("est_1rm", 0):
        broken.append("est_1rm")
    return broken


def detect_progressive_overload(workout_df: pd.DataFrame, exercise: str, current_volume: float) -> str:
    """Compare current_volume against the most recent PREVIOUS logged volume
    for the same exercise. Returns one of:
    'Performance Increased', 'Performance Maintained', 'Performance Decreased',
    or 'No Prior Data'."""
    if workout_df is None or workout_df.empty:
        return "No Prior Data"
    subset = workout_df[workout_df["exercise"] == exercise].copy()
    if subset.empty:
        return "No Prior Data"
    subset["date"] = pd.to_datetime(subset["date"], errors="coerce")
    subset = subset.sort_values("date")
    if subset.empty:
        return "No Prior Data"
    previous_volume = float(subset.iloc[-1]["volume"] or 0)
    if current_volume > previous_volume:
        return "Performance Increased"
    elif current_volume == previous_volume:
        return "Performance Maintained"
    else:
        return "Performance Decreased"


def volume_by_muscle_group(workout_df: pd.DataFrame) -> pd.DataFrame:
    if workout_df is None or workout_df.empty:
        return pd.DataFrame(columns=["muscle_group", "volume"])
    return workout_df.groupby("muscle_group", as_index=False)["volume"].sum()


def volume_trend(workout_df: pd.DataFrame, freq: str = "W") -> pd.DataFrame:
    """freq='W' weekly, 'M' monthly. Returns columns [period, volume]."""
    if workout_df is None or workout_df.empty:
        return pd.DataFrame(columns=["period", "volume"])
    df = workout_df.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])
    if df.empty:
        return pd.DataFrame(columns=["period", "volume"])
    grouped = df.set_index("date").resample(freq)["volume"].sum().reset_index()
    grouped.columns = ["period", "volume"]
    return grouped


# ----------------------------------------------------------------------
# Streaks
# ----------------------------------------------------------------------
def compute_streak(dates: list, reference_day: Optional[date] = None) -> int:
    """Given a list of date-like values (any dupes/None ok), compute the
    current consecutive-day streak ending today or yesterday (so a streak
    isn't broken just because today hasn't been logged yet)."""
    reference_day = reference_day or date.today()
    parsed = set()
    for d in dates:
        if d is None or (isinstance(d, float) and pd.isna(d)):
            continue
        try:
            parsed.add(pd.to_datetime(d).date())
        except Exception:
            continue
    if not parsed:
        return 0

    if reference_day in parsed:
        cursor = reference_day
    elif (reference_day - timedelta(days=1)) in parsed:
        cursor = reference_day - timedelta(days=1)
    else:
        return 0

    streak = 0
    while cursor in parsed:
        streak += 1
        cursor -= timedelta(days=1)
    return streak


# ----------------------------------------------------------------------
# Nutrition
# ----------------------------------------------------------------------
def daily_macro_summary(nutrition_df: pd.DataFrame, day: date) -> dict:
    if nutrition_df is None or nutrition_df.empty:
        return {"protein": 0.0, "carbs": 0.0, "fat": 0.0, "calories": 0.0}
    df = nutrition_df.copy()
    df["date_only"] = pd.to_datetime(df["date"], errors="coerce").dt.date
    todays = df[df["date_only"] == day]
    if todays.empty:
        return {"protein": 0.0, "carbs": 0.0, "fat": 0.0, "calories": 0.0}
    return {
        "protein": float(todays["protein"].sum() or 0),
        "carbs": float(todays["carbs"].sum() or 0),
        "fat": float(todays["fat"].sum() or 0),
        "calories": float(todays["calories"].sum() or 0),
    }


def macro_status(actual: dict, targets: dict) -> dict:
    status = {}
    protein_pct = (actual["protein"] / targets["protein"] * 100) if targets.get("protein") else 0
    status["protein"] = "Protein Goal Met" if protein_pct >= 100 else "Protein Low"
    cal_pct = (actual["calories"] / targets["calories"] * 100) if targets.get("calories") else 0
    if cal_pct > 110:
        status["calories"] = "Calories Too High"
    else:
        status["calories"] = "Calories On Target"
    return status


# ----------------------------------------------------------------------
# Body progress / goal prediction
# ----------------------------------------------------------------------
def goal_prediction(body_df: pd.DataFrame, goal_weight: float) -> dict:
    """Estimate the date the goal weight will be reached, based on the
    average daily weight-loss rate over the last 14 days of logged data."""
    result = {
        "current_weight": None,
        "rate_per_day": None,
        "days_remaining": None,
        "predicted_date": None,
        "message": "Not enough data yet - log your weight a few more times.",
    }
    if body_df is None or body_df.empty:
        return result

    df = body_df.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date", "weight"]).sort_values("date")
    if df.empty:
        return result

    current_weight = float(df.iloc[-1]["weight"])
    result["current_weight"] = current_weight

    cutoff = df.iloc[-1]["date"] - timedelta(days=14)
    window = df[df["date"] >= cutoff]
    if len(window) < 2:
        return result

    days_span = (window.iloc[-1]["date"] - window.iloc[0]["date"]).days
    weight_change = float(window.iloc[-1]["weight"]) - float(window.iloc[0]["weight"])
    if days_span <= 0:
        return result

    rate_per_day = weight_change / days_span  # negative = losing weight
    result["rate_per_day"] = round(rate_per_day, 4)

    if rate_per_day >= 0:
        result["message"] = "Weight isn't trending down yet over the last 14 days."
        return result

    remaining = current_weight - goal_weight
    if remaining <= 0:
        result["message"] = "Goal weight already reached!"
        result["days_remaining"] = 0
        result["predicted_date"] = date.today().isoformat()
        return result

    days_needed = remaining / abs(rate_per_day)
    predicted = date.today() + timedelta(days=round(days_needed))
    result["days_remaining"] = round(days_needed)
    result["predicted_date"] = predicted.isoformat()
    result["message"] = "On track based on your last 14 days."
    return result


# ----------------------------------------------------------------------
# Daily score
# ----------------------------------------------------------------------
def compute_daily_score(
    workout_logged: bool,
    cardio_logged: bool,
    protein_met: bool,
    calories_on_target: bool,
    body_checkin: bool,
) -> int:
    w = C.DAILY_SCORE_WEIGHTS
    score = 0
    score += w["workout"] if workout_logged else 0
    score += w["cardio"] if cardio_logged else 0
    score += w["protein"] if protein_met else 0
    score += w["calories"] if calories_on_target else 0
    score += w["body_checkin"] if body_checkin else 0
    return score
