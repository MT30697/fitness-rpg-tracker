"""
Reusable Streamlit UI building blocks used across every page so the app
has one consistent visual language.
"""
from __future__ import annotations

import streamlit as st

from utils import constants as C


def load_css() -> None:
    """Inject the custom dark theme CSS and hide Streamlit chrome."""
    try:
        css = C.CSS_FILE.read_text(encoding="utf-8")
    except FileNotFoundError:
        css = ""
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def page_header(title: str, icon: str = "", subtitle: str = "") -> None:
    st.markdown(f"## {icon} {title}" if icon else f"## {title}")
    if subtitle:
        st.markdown(f"<span style='color:{C.THEME_COLORS['muted']}'>{subtitle}</span>", unsafe_allow_html=True)
    st.write("")


def metric_card(label: str, value: str, sub: str = "", module: str | None = None) -> None:
    """module: an optional category name (e.g. 'workout', 'cardio') shown as
    a small uppercase tag at the top of the card. In the black/white theme,
    category is signalled by this text tag rather than by color."""
    tag_html = f"<div class='rpg-card-tag'>{module.upper()}</div>" if module else ""
    sub_html = f"<div class='rpg-metric-sub'>{sub}</div>" if sub else ""
    st.markdown(
        f"""
        <div class="rpg-card">
            {tag_html}
            <div class="rpg-metric-label">{label}</div>
            <div class="rpg-metric-value">{value}</div>
            {sub_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def progress_bar(label: str, value: float, max_value: float, suffix: str = "") -> None:
    max_value = max_value or 1
    pct = max(0, min(100, (value / max_value) * 100))
    st.markdown(
        f"""
        <div style="margin-bottom:10px;">
            <div style="display:flex; justify-content:space-between; font-size:0.85rem; color:{C.THEME_COLORS['text']};">
                <span>{label}</span>
                <span style="font-family:'JetBrains Mono', monospace;">{value:.0f}{suffix} / {max_value:.0f}{suffix}</span>
            </div>
            <div class="rpg-progress-wrap">
                <div class="rpg-progress-fill" style="width:{pct}%;"></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def badge(text: str, style: str = "info") -> str:
    """Returns badge HTML - caller wraps in st.markdown(..., unsafe_allow_html=True)."""
    return f"<span class='rpg-badge rpg-badge-{style}'>{text}</span>"


def render_badges(badges: list[tuple[str, str]]) -> None:
    """badges: list of (text, style) tuples."""
    html = " ".join(badge(t, s) for t, s in badges)
    st.markdown(html, unsafe_allow_html=True)


def status_to_style(status: str) -> str:
    mapping = {
        "Performance Increased": "success",
        "Performance Maintained": "info",
        "Performance Decreased": "danger",
        "No Prior Data": "locked",
        "Protein Goal Met": "success",
        "Protein Low": "warning",
        "Calories On Target": "success",
        "Calories Too High": "danger",
    }
    return mapping.get(status, "info")


def level_ring(level: int, xp_into_level: int, xp_per_level: int, total_xp: int, size: str = "md") -> None:
    """The app's signature element: a circular gold ring whose fill shows
    progress toward the next level, with the level number at its center.
    size: 'md' (sidebar/dashboard) or 'lg' (RPG System hero)."""
    pct = max(0, min(100, (xp_into_level / xp_per_level) * 100)) if xp_per_level else 0
    size_class = "level-ring level-ring--lg" if size == "lg" else "level-ring"
    st.markdown(
        f"""
        <div class="level-ring-wrap">
            <div class="{size_class}" style="--pct:{pct:.1f}%;">
                <div class="level-ring-inner">
                    <div class="level-tag">LV</div>
                    <div class="level-num">{level}</div>
                </div>
            </div>
            <div>
                <div class="level-side-label">TOTAL XP</div>
                <div class="level-side-value">{total_xp:,}</div>
                <div class="level-side-label" style="margin-top:6px;">{xp_into_level} / {xp_per_level} to next level</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def achievement_tile(name: str, icon: str, description: str, unlocked: bool, unlocked_date: str | None) -> None:
    css_class = "rpg-achievement rpg-achievement-unlocked" if unlocked else "rpg-achievement"
    icon_class = "rpg-achievement-icon" if unlocked else "rpg-achievement-locked-icon"
    sub = f"Unlocked {unlocked_date}" if unlocked and unlocked_date else ("Locked" if not unlocked else "Unlocked")
    st.markdown(
        f"""
        <div class="{css_class}">
            <div class="{icon_class}">{icon}</div>
            <div class="rpg-achievement-name">{name}</div>
            <div class="rpg-achievement-desc">{description}</div>
            <div class="rpg-achievement-sub">{sub}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
