"""
Optional Google Sheets storage backend.

This is used automatically when the app's `.streamlit/secrets.toml` has a
`[connections.gsheets]` block configured (the normal setup when deployed
to Streamlit Community Cloud, since that platform's local filesystem is
ephemeral and not safe for long-term data). When no such secret exists
(e.g. running locally on your own machine), `is_enabled()` returns False
and `data_manager.py` falls back to plain CSV/JSON files instead — this
module is then never touched.

Every CSV-shaped data file maps to one worksheet (tab) in a single Google
Sheet, with a matching name (e.g. data/workout_log.csv -> worksheet
"workout_log"). The three small JSON "documents" (settings, rpg_state,
achievements) are stored as JSON-encoded strings in a shared two-column
worksheet called "app_state", one row per document.
"""
from __future__ import annotations

import json

import pandas as pd
import streamlit as st

KV_WORKSHEET = "app_state"
KV_COLUMNS = ["key", "value"]


def is_enabled() -> bool:
    """True when secrets.toml has a [connections.gsheets] block."""
    try:
        return "gsheets" in st.secrets.get("connections", {})
    except Exception:
        return False


@st.cache_resource(show_spinner=False)
def _connection():
    from streamlit_gsheets import GSheetsConnection
    return st.connection("gsheets", type=GSheetsConnection)


def _empty(columns: list[str]) -> pd.DataFrame:
    return pd.DataFrame(columns=columns)


def ensure_worksheet(worksheet: str, columns: list[str]) -> None:
    """Create the worksheet with the right header row if it doesn't exist."""
    conn = _connection()
    try:
        conn.read(worksheet=worksheet, ttl=5)
    except Exception:
        try:
            conn.create(worksheet=worksheet, data=_empty(columns))
        except Exception:
            # Best-effort: if this also fails (e.g. a real permissions
            # problem), the next explicit read/write below will raise a
            # clear error the user can act on instead of failing silently.
            pass


def read_df(worksheet: str, columns: list[str], ttl: int = 5) -> pd.DataFrame:
    """Always returns a DataFrame with exactly `columns`, even if the
    worksheet is missing or empty — mirrors data_manager.load_csv.

    ttl=5 means repeated reads of the same worksheet within a 5-second
    window reuse a cached result instead of calling the Sheets API again.
    Streamlit reruns the whole script on every interaction, and a single
    page can read 4-5 worksheets, so without this a few page loads will
    burn through Google's per-minute read quota."""
    conn = _connection()
    try:
        df = conn.read(worksheet=worksheet, ttl=ttl)
    except Exception:
        return _empty(columns)
    if df is None or df.empty:
        return _empty(columns)
    df = df.dropna(how="all")
    for col in columns:
        if col not in df.columns:
            df[col] = None
    return df[columns].reset_index(drop=True)


def write_df(worksheet: str, df: pd.DataFrame, columns: list[str]) -> None:
    conn = _connection()
    out = df.reindex(columns=columns)
    conn.update(worksheet=worksheet, data=out)


def read_kv(key: str, default: dict) -> dict:
    df = read_df(KV_WORKSHEET, KV_COLUMNS)
    match = df[df["key"] == key] if not df.empty else df
    if match.empty:
        return dict(default)
    raw = match.iloc[0]["value"]
    try:
        return json.loads(raw) if raw else dict(default)
    except (json.JSONDecodeError, TypeError):
        return dict(default)


def write_kv(key: str, data: dict) -> None:
    df = read_df(KV_WORKSHEET, KV_COLUMNS)
    payload = json.dumps(data, default=str)
    if not df.empty and (df["key"] == key).any():
        df.loc[df["key"] == key, "value"] = payload
    else:
        df = pd.concat([df, pd.DataFrame([{"key": key, "value": payload}])], ignore_index=True)
    write_df(KV_WORKSHEET, df, KV_COLUMNS)
