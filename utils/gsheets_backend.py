"""
Optional Google Sheets storage backend.
Auto-detected from secrets.toml. Falls back to local CSV/JSON when absent.
All writes have retry logic and error handling so a transient API hiccup
won't crash the app.
"""
from __future__ import annotations
import json
import time
import pandas as pd
import streamlit as st

KV_WORKSHEET = "app_state"
KV_COLUMNS = ["key", "value"]


def is_enabled() -> bool:
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
    conn = _connection()
    try:
        conn.read(worksheet=worksheet, ttl=5)
    except Exception:
        try:
            conn.create(worksheet=worksheet, data=_empty(columns))
        except Exception:
            pass


def read_df(worksheet: str, columns: list[str], ttl: int = 5) -> pd.DataFrame:
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


def write_df(worksheet: str, df: pd.DataFrame, columns: list[str]) -> bool:
    """Write df to worksheet. Retries once on API rate-limit errors.
    Returns True on success, False on failure (so callers can handle)."""
    conn = _connection()
    out = df.reindex(columns=columns)
    for attempt in range(2):
        try:
            conn.update(worksheet=worksheet, data=out)
            return True
        except Exception as e:
            err = str(e).lower()
            if attempt == 0 and ("quota" in err or "rate" in err or "429" in err or "resource" in err):
                time.sleep(3)
                continue
            # Second failure or non-rate-limit error
            st.warning(f"⚠️ Could not save to Google Sheets: {e}. Data may not be saved — try again.")
            return False
    return False


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
