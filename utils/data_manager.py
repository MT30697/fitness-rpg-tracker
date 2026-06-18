"""
Data access layer for Fitness RPG Tracker.

Every read/write goes through this module so the rest of the app never
touches storage directly. Two backends are supported, chosen
automatically and transparently:

- Local CSV/JSON files under data/ (default — used whenever you run the
  app on your own machine, e.g. `streamlit run app.py`).
- Google Sheets (used automatically when `.streamlit/secrets.toml` has a
  [connections.gsheets] block — the setup for deploying on Streamlit
  Community Cloud, whose local filesystem is not persistent).

Every public function below has the exact same signature and behaviour
in both modes, so pages/, calculations.py and rpg_engine.py never need
to know or care which backend is active.
"""
from __future__ import annotations

import json
import uuid
from datetime import date, datetime
from typing import Any

import streamlit as st
import pandas as pd

from utils import constants as C
from utils import gsheets_backend as GS


# ----------------------------------------------------------------------
# Bootstrapping
# ----------------------------------------------------------------------
@st.cache_resource(show_spinner=False)
def ensure_data_files() -> None:
    """Create the data folder/files (local mode) or worksheets (Sheets
    mode) with correct headers/defaults if they don't exist yet.

    Cached with cache_resource: Streamlit reruns the whole script on
    every interaction, but this check only ever needs to happen once per
    running app (worksheets/files don't need re-verifying every click) —
    without caching, this alone is enough Sheets API calls to burn
    through Google's per-minute read quota within a few page loads."""
    if GS.is_enabled():
        GS.ensure_worksheet(C.EXERCISE_LIBRARY_FILE.stem, C.EXERCISE_LIBRARY_COLUMNS)
        GS.ensure_worksheet(C.WORKOUT_LOG_FILE.stem, C.WORKOUT_LOG_COLUMNS)
        GS.ensure_worksheet(C.CARDIO_LOG_FILE.stem, C.CARDIO_LOG_COLUMNS)
        GS.ensure_worksheet(C.NUTRITION_LOG_FILE.stem, C.NUTRITION_LOG_COLUMNS)
        GS.ensure_worksheet(C.BODY_PROGRESS_FILE.stem, C.BODY_PROGRESS_COLUMNS)
        GS.ensure_worksheet(GS.KV_WORKSHEET, GS.KV_COLUMNS)

        if not GS.read_kv(C.SETTINGS_FILE.stem, {}):
            defaults = dict(C.DEFAULT_SETTINGS)
            defaults["start_date"] = date.today().isoformat()
            GS.write_kv(C.SETTINGS_FILE.stem, defaults)
        if not GS.read_kv(C.RPG_STATE_FILE.stem, {}):
            GS.write_kv(C.RPG_STATE_FILE.stem, dict(C.DEFAULT_RPG_STATE))
        if not GS.read_kv(C.ACHIEVEMENTS_FILE.stem, {}):
            achievements = {
                a["id"]: {**a, "unlocked": False, "unlocked_date": None}
                for a in C.ACHIEVEMENT_DEFS
            }
            GS.write_kv(C.ACHIEVEMENTS_FILE.stem, achievements)
        if not GS.read_kv(C.WORKOUT_TEMPLATES_FILE.stem, {}):
            GS.write_kv(C.WORKOUT_TEMPLATES_FILE.stem, dict(C.DEFAULT_WORKOUT_TEMPLATES))
        return

    C.DATA_DIR.mkdir(parents=True, exist_ok=True)
    C.BODY_PHOTOS_DIR.mkdir(parents=True, exist_ok=True)

    _ensure_csv(C.EXERCISE_LIBRARY_FILE, C.EXERCISE_LIBRARY_COLUMNS)
    _ensure_csv(C.WORKOUT_LOG_FILE, C.WORKOUT_LOG_COLUMNS)
    _ensure_csv(C.CARDIO_LOG_FILE, C.CARDIO_LOG_COLUMNS)
    _ensure_csv(C.NUTRITION_LOG_FILE, C.NUTRITION_LOG_COLUMNS)
    _ensure_csv(C.BODY_PROGRESS_FILE, C.BODY_PROGRESS_COLUMNS)

    if not C.SETTINGS_FILE.exists():
        defaults = dict(C.DEFAULT_SETTINGS)
        defaults["start_date"] = date.today().isoformat()
        save_json(C.SETTINGS_FILE, defaults)

    if not C.RPG_STATE_FILE.exists():
        save_json(C.RPG_STATE_FILE, dict(C.DEFAULT_RPG_STATE))

    if not C.ACHIEVEMENTS_FILE.exists():
        achievements = {
            a["id"]: {**a, "unlocked": False, "unlocked_date": None}
            for a in C.ACHIEVEMENT_DEFS
        }
        save_json(C.ACHIEVEMENTS_FILE, achievements)

    if not C.WORKOUT_TEMPLATES_FILE.exists():
        save_json(C.WORKOUT_TEMPLATES_FILE, dict(C.DEFAULT_WORKOUT_TEMPLATES))


def _ensure_csv(path, columns: list[str]) -> None:
    if not path.exists():
        pd.DataFrame(columns=columns).to_csv(path, index=False)


# ----------------------------------------------------------------------
# Generic CSV helpers (path identifies a worksheet by its stem in
# Sheets mode, and a local file in local mode — callers never branch)
# ----------------------------------------------------------------------
def generate_id() -> str:
    return uuid.uuid4().hex[:12]


def load_csv(path, columns: list[str]) -> pd.DataFrame:
    """Always returns a DataFrame with the expected columns, even if the
    file/worksheet is missing or empty."""
    if GS.is_enabled():
        return GS.read_df(path.stem, columns)
    try:
        if not path.exists() or path.stat().st_size == 0:
            return pd.DataFrame(columns=columns)
        df = pd.read_csv(path)
        if df.empty:
            return pd.DataFrame(columns=columns)
        for col in columns:
            if col not in df.columns:
                df[col] = None
        return df[columns]
    except (pd.errors.EmptyDataError, FileNotFoundError):
        return pd.DataFrame(columns=columns)


def append_csv_row(path, row: dict[str, Any], columns: list[str]) -> None:
    df = load_csv(path, columns)
    new_row = pd.DataFrame([{c: row.get(c) for c in columns}])
    df = pd.concat([df, new_row], ignore_index=True)
    if GS.is_enabled():
        GS.write_df(path.stem, df, columns)
    else:
        df.to_csv(path, index=False)


def update_csv_row(path, columns: list[str], id_col: str, id_value: str, updates: dict[str, Any]) -> bool:
    df = load_csv(path, columns)
    mask = df[id_col].astype(str) == str(id_value)
    if not mask.any():
        return False
    # Cast to object dtype first: pandas infers strict per-column dtypes
    # (e.g. float64) from existing data, and will raise LossySetitemError
    # if we then try to assign an incompatible type (e.g. a string into a
    # float column) via .loc. Object dtype writes back identically in
    # both backends, so this is safe and avoids the crash on edit.
    df = df.astype(object)
    row_idx = df.index[mask]
    for k, v in updates.items():
        if k in columns:
            df.loc[row_idx, k] = v
    if GS.is_enabled():
        GS.write_df(path.stem, df, columns)
    else:
        df.to_csv(path, index=False)
    return True


def delete_csv_row(path, columns: list[str], id_col: str, id_value: str) -> bool:
    df = load_csv(path, columns)
    mask = df[id_col].astype(str) == str(id_value)
    if not mask.any():
        return False
    df = df[~mask]
    if GS.is_enabled():
        GS.write_df(path.stem, df, columns)
    else:
        df.to_csv(path, index=False)
    return True


# ----------------------------------------------------------------------
# JSON / document helpers (path identifies a document by its stem in
# Sheets mode — stored as a row in the shared "app_state" worksheet)
# ----------------------------------------------------------------------
def load_json(path, default: dict) -> dict:
    if GS.is_enabled():
        return GS.read_kv(path.stem, default)
    try:
        if not path.exists() or path.stat().st_size == 0:
            return dict(default)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if data else dict(default)
    except (json.JSONDecodeError, FileNotFoundError):
        return dict(default)


def save_json(path, data: dict) -> None:
    if GS.is_enabled():
        GS.write_kv(path.stem, data)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)


# ----------------------------------------------------------------------
# Domain-specific convenience wrappers
# ----------------------------------------------------------------------
def load_settings() -> dict:
    return load_json(C.SETTINGS_FILE, C.DEFAULT_SETTINGS)


def save_settings(settings: dict) -> None:
    save_json(C.SETTINGS_FILE, settings)


def load_exercise_library() -> pd.DataFrame:
    return load_csv(C.EXERCISE_LIBRARY_FILE, C.EXERCISE_LIBRARY_COLUMNS)


def load_workout_templates() -> dict:
    return load_json(C.WORKOUT_TEMPLATES_FILE, C.DEFAULT_WORKOUT_TEMPLATES)


def save_workout_templates(templates: dict) -> None:
    save_json(C.WORKOUT_TEMPLATES_FILE, templates)


def ensure_exercises_in_library(exercises: list[dict]) -> None:
    """Auto-add any of these {exercise_name, muscle_group} pairs to the
    Exercise Library if not already present, so they also show up in the
    normal Workout Log dropdown. Used when seeding/using templates."""
    library_df = load_exercise_library()
    existing = set(library_df["exercise_name"].str.lower()) if not library_df.empty else set()
    for ex in exercises:
        if ex["exercise_name"].lower() not in existing:
            append_csv_row(C.EXERCISE_LIBRARY_FILE, {
                "exercise_id": generate_id(),
                "exercise_name": ex["exercise_name"],
                "muscle_group": ex["muscle_group"],
                "equipment": "Other",
                "notes": "",
                "created_at": now_iso(),
            }, C.EXERCISE_LIBRARY_COLUMNS)
            existing.add(ex["exercise_name"].lower())


def load_workout_log() -> pd.DataFrame:
    df = load_csv(C.WORKOUT_LOG_FILE, C.WORKOUT_LOG_COLUMNS)
    return _coerce_numeric(df, C.NUMERIC_COLUMNS["workout"])


def load_cardio_log() -> pd.DataFrame:
    df = load_csv(C.CARDIO_LOG_FILE, C.CARDIO_LOG_COLUMNS)
    return _coerce_numeric(df, C.NUMERIC_COLUMNS["cardio"])


def load_nutrition_log() -> pd.DataFrame:
    df = load_csv(C.NUTRITION_LOG_FILE, C.NUTRITION_LOG_COLUMNS)
    return _coerce_numeric(df, C.NUMERIC_COLUMNS["nutrition"])


def load_body_progress() -> pd.DataFrame:
    df = load_csv(C.BODY_PROGRESS_FILE, C.BODY_PROGRESS_COLUMNS)
    return _coerce_numeric(df, C.NUMERIC_COLUMNS["body"])


def _coerce_numeric(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")
