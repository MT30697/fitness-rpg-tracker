"""
Reusable Streamlit UI building blocks used across every page so the app
has one consistent visual language.
"""
from __future__ import annotations

import streamlit as st

from utils import constants as C

# Base64-encoded PNG used as the iPhone home-screen icon (apple-touch-icon).
# Generated once and baked in here so it works identically locally and on
# Streamlit Community Cloud, with no separate static-file hosting needed.
_APPLE_TOUCH_ICON_B64 = (
    "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"
)


def load_css() -> None:
    """Inject the custom dark theme CSS and hide Streamlit chrome."""
    try:
        css = C.CSS_FILE.read_text(encoding="utf-8")
    except FileNotFoundError:
        css = ""
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def inject_pwa_meta() -> None:
    """Add the meta tags iOS Safari needs to launch this app full-screen,
    with no address bar, when opened from a Home Screen icon ("Add to
    Home Screen"). Streamlit doesn't expose an API to edit <head>, so this
    runs a tiny script inside a 0-size component iframe that reaches into
    the parent document (same origin, so this is allowed) and adds the
    tags itself.

    Important: Safari reads these tags at the moment you tap "Add to Home
    Screen", not afterward — if you already added the icon before this
    was in place, remove that icon and re-add it once for it to take
    effect in standalone (no browser chrome) mode."""
    st.components.v1.html(
        """
        <script>
        const metas = [
            {name: "apple-mobile-web-app-capable", content: "yes"},
            {name: "mobile-web-app-capable", content: "yes"},
            {name: "apple-mobile-web-app-status-bar-style", content: "black-translucent"},
            {name: "apple-mobile-web-app-title", content: "Fitness RPG"},
        ];
        metas.forEach(function (m) {
            var tag = parent.document.querySelector("meta[name='" + m.name + "']");
            if (!tag) {
                tag = parent.document.createElement("meta");
                tag.setAttribute("name", m.name);
                parent.document.head.appendChild(tag);
            }
            tag.setAttribute("content", m.content);
        });
        parent.document.title = "Fitness RPG Tracker";

        var iconHref = "data:image/png;base64,__ICON_B64__";
        [
            {rel: "apple-touch-icon", href: iconHref},
            {rel: "icon", href: iconHref},
        ].forEach(function (l) {
            var existing = parent.document.querySelectorAll("link[rel='" + l.rel + "']");
            existing.forEach(function (e) { e.parentNode.removeChild(e); });
            var link = parent.document.createElement("link");
            link.setAttribute("rel", l.rel);
            link.setAttribute("href", l.href);
            parent.document.head.appendChild(link);
        });
        </script>
        """.replace("__ICON_B64__", _APPLE_TOUCH_ICON_B64),
        height=0,
        width=0,
    )


def _fmt_decimal(v) -> str:
    try:
        v = float(v)
        return str(int(v)) if v == int(v) else str(v)
    except (TypeError, ValueError):
        return "0"


def decimal_input(label: str, value: float = 0.0, key: str | None = None, help: str | None = None) -> float:
    """Phone-keyboard-friendly decimal number input.

    st.number_input uses HTML <input type='number'> which only accepts '.'
    as the decimal separator, but many phone keyboards (especially on
    Vietnamese locale) type ',' instead — so '32,5' gets silently dropped
    and the field shows 0 or stays blank.

    This renders a plain text field and accepts both '32.5' and '32,5'.
    Works inside and outside st.form blocks."""
    default_str = _fmt_decimal(value)
    raw = st.text_input(
        label,
        value=default_str,
        key=key,
        help=(help or "") + " (nhập số, dùng dấu . hoặc , đều được)",
        placeholder="vd: 32.5",
    )
    raw = (raw or "").strip().replace(",", ".")
    if not raw:
        return 0.0
    try:
        result = float(raw)
        return max(0.0, result)
    except ValueError:
        st.caption(f"⚠️ '{raw}' không phải số hợp lệ — đang dùng 0.")
        return 0.0


def page_header(title: str, icon: str = "", subtitle: str = "") -> None:
    st.markdown(f"## {icon} {title}" if icon else f"## {title}")
    if subtitle:
        st.markdown(f"<span style='color:{C.THEME_COLORS['muted']}'>{subtitle}</span>", unsafe_allow_html=True)
    st.write("")


_MODULE_ICONS = {
    "workout": "🏋️",
    "cardio": "🏃",
    "nutrition": "🍽️",
    "body": "⚖️",
    "score": "⭐",
}


def metric_card(label: str, value: str, sub: str = "", module: str | None = None) -> None:
    """module: an optional category ('workout' | 'cardio' | 'nutrition' |
    'body' | 'score') shown as a small colored icon badge at the top of
    the card, matching iOS Health/Fitness-style tiles."""
    icon_html = ""
    if module:
        icon = _MODULE_ICONS.get(module, "•")
        icon_html = f"<div class='rpg-card-tag rpg-card-tag--{module}'>{icon}</div>"
    sub_html = f"<div class='rpg-metric-sub'>{sub}</div>" if sub else ""
    st.markdown(
        f"""
        <div class="rpg-card">
            {icon_html}
            <div class="rpg-metric-label">{label}</div>
            <div class="rpg-metric-value">{value}</div>
            {sub_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def progress_bar(label: str, value: float, max_value: float, suffix: str = "", color: str = "blue") -> None:
    """color: 'blue' | 'green' | 'red' | 'purple' | 'yellow' — maps to the
    same category palette used elsewhere in the app."""
    color_map = {
        "blue": "var(--blue)", "green": "var(--green)", "red": "var(--red)",
        "purple": "var(--purple)", "yellow": "var(--yellow)",
    }
    fill = color_map.get(color, "var(--blue)")
    max_value = max_value or 1
    pct = max(0, min(100, (value / max_value) * 100))
    st.markdown(
        f"""
        <div style="margin-bottom:10px;">
            <div style="display:flex; justify-content:space-between; font-size:0.85rem; color:{C.THEME_COLORS['text']};">
                <span>{label}</span>
                <span style="color:{C.THEME_COLORS['muted']};">{value:.0f}{suffix} / {max_value:.0f}{suffix}</span>
            </div>
            <div class="rpg-progress-wrap">
                <div class="rpg-progress-fill" style="width:{pct}%; background:{fill};"></div>
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


_TAB_DEFS = [
    ("dashboard", "🏠", "Dashboard", "pages/dashboard.py"),
    ("workout", "🏋️", "Workout", "pages/workout_log.py"),
    ("cardio", "🏃", "Cardio", "pages/cardio.py"),
    ("nutrition", "🍽️", "Nutrition", "pages/nutrition.py"),
    ("more", "🧩", "More", "pages/more.py"),
]


def bottom_tab_bar(active: str) -> None:
    """The app's primary navigation: a fixed bottom tab bar with 5 items.
    Exercise Library, Body Progress, RPG System, and Settings live behind
    the "more" tab (call with active="more" from those pages too, so the
    tab bar still shows where you are).

    active: 'dashboard' | 'workout' | 'cardio' | 'nutrition' | 'more'

    Built from real st.page_link calls (not raw <a> tags) so Streamlit's
    own page routing keeps working — only the current tab is rendered as
    plain non-clickable text instead of a self-link."""
    with st.container(key="bottom_tab_bar"):
        cols = st.columns(5)
        for col, (key, icon, label, path) in zip(cols, _TAB_DEFS):
            with col:
                if key == active:
                    st.markdown(
                        f"""
                        <div class="tab-item">
                            <div class="tab-icon">{icon}</div>
                            <div class="tab-label">{label}</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                else:
                    st.page_link(path, label=label, icon=icon)


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
