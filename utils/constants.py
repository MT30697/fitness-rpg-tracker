"""
Central constants for Fitness RPG Tracker.
Every other module imports paths, column schemas, option lists and
game-balance numbers from here so there is a single source of truth.
"""
from __future__ import annotations
from pathlib import Path

# ----------------------------------------------------------------------
# Paths
# ----------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
BODY_PHOTOS_DIR = DATA_DIR / "body_photos"
ASSETS_DIR = BASE_DIR / "assets"

SETTINGS_FILE = DATA_DIR / "settings.json"
ACHIEVEMENTS_FILE = DATA_DIR / "achievements.json"
RPG_STATE_FILE = DATA_DIR / "rpg_state.json"

EXERCISE_LIBRARY_FILE = DATA_DIR / "exercise_library.csv"
WORKOUT_LOG_FILE = DATA_DIR / "workout_log.csv"
CARDIO_LOG_FILE = DATA_DIR / "cardio_log.csv"
NUTRITION_LOG_FILE = DATA_DIR / "nutrition_log.csv"
BODY_PROGRESS_FILE = DATA_DIR / "body_progress.csv"

CSS_FILE = ASSETS_DIR / "style.css"

# ----------------------------------------------------------------------
# Option lists
# ----------------------------------------------------------------------
MUSCLE_GROUPS = ["Chest", "Back", "Shoulders", "Arms", "Legs", "Core", "Cardio", "Other"]
EQUIPMENT_TYPES = ["Barbell", "Dumbbell", "Machine", "Cable", "Bodyweight", "Other"]
CARDIO_TYPES = ["Walking", "Running", "Treadmill", "Cycling", "Other"]
MEAL_TYPES = ["Breakfast", "Lunch", "Dinner", "Snack", "Supplement"]
WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

# ----------------------------------------------------------------------
# CSV column schemas (order matters - matches how rows are written)
# ----------------------------------------------------------------------
EXERCISE_LIBRARY_COLUMNS = [
    "exercise_id", "exercise_name", "muscle_group", "equipment", "notes", "created_at",
]
WORKOUT_LOG_COLUMNS = [
    "log_id", "date", "muscle_group", "exercise", "sets", "reps", "weight",
    "rpe", "notes", "volume", "est_1rm", "is_pr", "created_at",
]
CARDIO_LOG_COLUMNS = [
    "log_id", "date", "type", "duration", "distance", "speed", "incline",
    "steps", "calories_burned", "notes", "created_at",
]
NUTRITION_LOG_COLUMNS = [
    "log_id", "date", "meal_type", "food_name", "protein", "carbs", "fat",
    "calories", "notes", "created_at",
]
BODY_PROGRESS_COLUMNS = [
    "log_id", "date", "weight", "waist", "body_fat", "photo", "notes", "created_at",
]

# Numeric columns per file - used for safe parsing
NUMERIC_COLUMNS = {
    "workout": ["sets", "reps", "weight", "rpe", "volume", "est_1rm"],
    "cardio": ["duration", "distance", "speed", "incline", "steps", "calories_burned"],
    "nutrition": ["protein", "carbs", "fat", "calories"],
    "body": ["weight", "waist", "body_fat"],
}

# ----------------------------------------------------------------------
# Default settings.json content
# ----------------------------------------------------------------------
DEFAULT_SETTINGS = {
    "height_cm": 179,
    "current_weight_kg": 86,
    "goal_weight_kg": 80,
    "waist_cm": None,
    "start_date": None,  # filled in with today's date on first run
    "nutrition_targets": {
        "calories": 2400,
        "protein": 205,
        "carbs": 267,
        "fat": 67,
    },
    "cardio_reminder_time": "06:00",
    "gym_reminder_time": "14:00",
    "workout_days": ["Monday", "Wednesday", "Friday"],
}

# ----------------------------------------------------------------------
# RPG / XP rules
# ----------------------------------------------------------------------
XP_RULES = {
    "workout_logged": 100,
    "cardio_logged": 50,
    "protein_goal_met": 50,
    "body_checkin": 20,
    "new_pr": 200,
    "weekly_goal_completed": 300,
}

XP_PER_LEVEL = 1000

DEFAULT_RPG_STATE = {
    "xp": 0,
    "level": 1,
    "xp_log": [],          # list of {date, amount, reason}
    "weekly_goal_awarded": [],  # list of iso-week strings already rewarded
}

# ----------------------------------------------------------------------
# Achievements
# ----------------------------------------------------------------------
ACHIEVEMENT_DEFS = [
    {"id": "first_workout", "name": "First Workout", "icon": "🏋️",
     "description": "Log your very first workout."},
    {"id": "seven_day_warrior", "name": "7 Day Warrior", "icon": "🔥",
     "description": "Reach a 7-day workout streak."},
    {"id": "protein_machine", "name": "Protein Machine", "icon": "🍗",
     "description": "Hit your protein goal on 7 different days."},
    {"id": "cardio_starter", "name": "Cardio Starter", "icon": "🏃",
     "description": "Log your first cardio session."},
    {"id": "fat_loss_start", "name": "Fat Loss Start", "icon": "📉",
     "description": "Log your first body check-in."},
    {"id": "five_kilos_down", "name": "Five Kilos Down", "icon": "⚖️",
     "description": "Lose 5kg from your starting weight."},
    {"id": "pr_hunter", "name": "PR Hunter", "icon": "🏆",
     "description": "Set 5 personal records."},
    {"id": "consistency_beast", "name": "Consistency Beast", "icon": "💪",
     "description": "Reach a 30-day workout streak."},
    {"id": "ten_k_steps", "name": "10K Steps", "icon": "👟",
     "description": "Log 10,000 steps in a single day."},
    {"id": "goal_weight", "name": "Goal Weight", "icon": "🎯",
     "description": "Reach your goal weight."},
]

# ----------------------------------------------------------------------
# Daily score weights (sum = 100)
# ----------------------------------------------------------------------
DAILY_SCORE_WEIGHTS = {
    "workout": 30,
    "cardio": 20,
    "protein": 25,
    "calories": 15,
    "body_checkin": 10,
}

THEME_COLORS = {
    "bg": "#000000",
    "card": "#070707",
    "border": "rgba(255,255,255,0.18)",
    "accent": "#ffffff",       # primary white accent — XP / level / signature
    "accent2": "#ffffff",
    "success": "#7fe3a3",
    "warning": "#e8c25e",
    "danger": "#ef6a5b",
    "text": "#f5f5f5",
    "muted": "rgba(245,245,245,0.55)",
}

# Category labels shown as small text tags on stat cards (rpg-card-tag) —
# in the black/white technical theme, category is signalled by text, not
# by color, so this is just the canonical display name per module.
MODULE_LABELS = {
    "workout": "WORKOUT",
    "cardio": "CARDIO",
    "nutrition": "NUTRITION",
    "body": "BODY",
    "rpg": "LEVEL",
}
