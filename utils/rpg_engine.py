"""
Gamification engine: XP, levels, achievements.
"""
from __future__ import annotations

from datetime import date
from typing import Optional

from utils import constants as C
from utils import data_manager as DM


# ----------------------------------------------------------------------
# XP / Levels
# ----------------------------------------------------------------------
def get_level_info(xp: int) -> dict:
    level = xp // C.XP_PER_LEVEL + 1
    xp_into_level = xp % C.XP_PER_LEVEL
    xp_needed_next = C.XP_PER_LEVEL - xp_into_level
    progress_pct = xp_into_level / C.XP_PER_LEVEL * 100
    return {
        "level": level,
        "xp": xp,
        "xp_into_level": xp_into_level,
        "xp_needed_next": xp_needed_next,
        "progress_pct": round(progress_pct, 1),
    }


def award_xp(reason_key: str, custom_amount: Optional[int] = None) -> dict:
    """Award XP for a given reason key (must exist in C.XP_RULES unless a
    custom_amount is supplied). Persists state and returns updated level info
    plus whether a level-up occurred."""
    state = DM.load_json(C.RPG_STATE_FILE, C.DEFAULT_RPG_STATE)
    amount = custom_amount if custom_amount is not None else C.XP_RULES.get(reason_key, 0)

    old_level = get_level_info(state.get("xp", 0))["level"]
    state["xp"] = int(state.get("xp", 0)) + int(amount)
    new_info = get_level_info(state["xp"])
    state["level"] = new_info["level"]

    log_entry = {"date": date.today().isoformat(), "amount": amount, "reason": reason_key}
    state.setdefault("xp_log", []).append(log_entry)

    DM.save_json(C.RPG_STATE_FILE, state)

    return {
        **new_info,
        "leveled_up": new_info["level"] > old_level,
        "amount_awarded": amount,
    }


def load_rpg_state() -> dict:
    return DM.load_json(C.RPG_STATE_FILE, C.DEFAULT_RPG_STATE)


# ----------------------------------------------------------------------
# Achievements
# ----------------------------------------------------------------------
def load_achievements() -> dict:
    default = {
        a["id"]: {**a, "unlocked": False, "unlocked_date": None}
        for a in C.ACHIEVEMENT_DEFS
    }
    return DM.load_json(C.ACHIEVEMENTS_FILE, default)


def _unlock(achievements: dict, achievement_id: str) -> bool:
    """Marks an achievement unlocked if not already. Returns True if newly unlocked."""
    if achievement_id not in achievements:
        return False
    if achievements[achievement_id].get("unlocked"):
        return False
    achievements[achievement_id]["unlocked"] = True
    achievements[achievement_id]["unlocked_date"] = date.today().isoformat()
    return True


def check_achievements(context: dict) -> list[dict]:
    """Evaluate all achievement conditions against the supplied context dict
    and unlock any that are newly satisfied. Persists achievements.json.

    Expected context keys (all optional, missing -> treated as not met):
        total_workouts: int
        workout_streak: int
        protein_goal_met_days: int
        total_cardio_sessions: int
        total_body_checkins: int
        starting_weight: float
        current_weight: float
        goal_weight: float
        total_prs: int
        max_steps_single_day: float
    """
    achievements = load_achievements()
    newly_unlocked = []

    def maybe(aid, condition):
        if condition and _unlock(achievements, aid):
            newly_unlocked.append(achievements[aid])

    maybe("first_workout", context.get("total_workouts", 0) >= 1)
    maybe("seven_day_warrior", context.get("workout_streak", 0) >= 7)
    maybe("protein_machine", context.get("protein_goal_met_days", 0) >= 7)
    maybe("cardio_starter", context.get("total_cardio_sessions", 0) >= 1)
    maybe("fat_loss_start", context.get("total_body_checkins", 0) >= 1)

    starting = context.get("starting_weight")
    current = context.get("current_weight")
    if starting is not None and current is not None:
        maybe("five_kilos_down", (starting - current) >= 5)

    maybe("pr_hunter", context.get("total_prs", 0) >= 5)
    maybe("consistency_beast", context.get("workout_streak", 0) >= 30)
    maybe("ten_k_steps", (context.get("max_steps_single_day") or 0) >= 10000)

    goal = context.get("goal_weight")
    if current is not None and goal is not None:
        maybe("goal_weight", current <= goal)

    DM.save_json(C.ACHIEVEMENTS_FILE, achievements)
    return newly_unlocked


def maybe_award_weekly_goal(workouts_this_week: int, target_workouts_per_week: int = 3) -> bool:
    """Award the one-time-per-week 'Weekly Goal Completed' XP bonus if the
    user hit their target number of workouts this ISO week and hasn't
    already been rewarded for it."""
    state = DM.load_json(C.RPG_STATE_FILE, C.DEFAULT_RPG_STATE)
    iso_week = date.today().isocalendar()
    week_key = f"{iso_week[0]}-W{iso_week[1]:02d}"
    already = week_key in state.get("weekly_goal_awarded", [])
    if already or workouts_this_week < target_workouts_per_week:
        return False
    award_xp("weekly_goal_completed")
    state = DM.load_json(C.RPG_STATE_FILE, C.DEFAULT_RPG_STATE)
    state.setdefault("weekly_goal_awarded", []).append(week_key)
    DM.save_json(C.RPG_STATE_FILE, state)
    return True

