"""Workout Templates - create your own saved routines (or use the seeded
starter ones), then quick-log a whole session in one go instead of
selecting each exercise manually every time."""
from __future__ import annotations

from datetime import date

import streamlit as st

from components.ui import bottom_tab_bar, page_header
from utils import constants as C
from utils import data_manager as DM
from utils import rpg_engine as RPG
from utils import workout_actions as WA

page_header("Workout Templates", "🗂️", "Tự tạo buổi tập của riêng bạn, log nhanh mỗi lần lặp lại.")

for key in ("selected_template", "editing_template", "draft_exercises", "confirm_delete"):
    if key not in st.session_state:
        st.session_state[key] = None
if st.session_state["draft_exercises"] is None:
    st.session_state["draft_exercises"] = []

templates = DM.load_workout_templates()

# ----------------------------------------------------------------------
# Mode 1: Create / edit a template
# ----------------------------------------------------------------------
if st.session_state["editing_template"] is not None:
    editing_key = st.session_state["editing_template"]
    is_new = editing_key == "__new__"

    if is_new and not st.session_state["draft_exercises"] and "draft_name" not in st.session_state:
        st.session_state["draft_name"] = ""
    if not is_new and "draft_name" not in st.session_state:
        st.session_state["draft_name"] = templates[editing_key]["name"]
        st.session_state["draft_exercises"] = list(templates[editing_key]["exercises"])

    st.markdown("#### " + ("➕ Buổi tập mới" if is_new else "✏️ Sửa buổi tập"))
    name = st.text_input("Tên buổi tập (vd: Day 8 — Pull B)", value=st.session_state.get("draft_name", ""))
    st.session_state["draft_name"] = name

    st.write("")
    if st.session_state["draft_exercises"]:
        st.caption("Các bài đã thêm:")
        for i, ex in enumerate(st.session_state["draft_exercises"]):
            c1, c2 = st.columns([5, 1])
            with c1:
                st.markdown(f"**{ex['exercise_name']}** — {ex['muscle_group']} · {ex['sets']}x{ex['reps_display']}")
            with c2:
                if st.button("🗑️", key=f"rm_draft_{i}"):
                    st.session_state["draft_exercises"].pop(i)
                    st.rerun()
    else:
        st.caption("Chưa có bài tập nào — thêm bài đầu tiên bên dưới.")

    st.divider()
    st.caption("Thêm bài tập")
    with st.form("add_exercise_to_draft", clear_on_submit=True):
        ac1, ac2 = st.columns(2)
        with ac1:
            ex_name = st.text_input("Tên bài tập")
            ex_muscle = st.selectbox("Nhóm cơ", C.MUSCLE_GROUPS)
        with ac2:
            ex_sets = st.number_input("Sets", min_value=1, step=1, value=3)
            ex_reps = st.number_input("Reps mục tiêu", min_value=1, step=1, value=10)
        add_submitted = st.form_submit_button("➕ Thêm bài này vào buổi", use_container_width=True)
        if add_submitted:
            if not ex_name.strip():
                st.error("Nhập tên bài tập trước.")
            else:
                st.session_state["draft_exercises"].append({
                    "exercise_name": ex_name.strip(),
                    "muscle_group": ex_muscle,
                    "sets": int(ex_sets),
                    "reps_default": int(ex_reps),
                    "reps_display": str(int(ex_reps)),
                })
                st.rerun()

    st.divider()
    col_save, col_cancel = st.columns(2)
    with col_save:
        if st.button("💾 Lưu buổi tập", use_container_width=True):
            if not name.strip():
                st.error("Nhập tên buổi tập trước khi lưu.")
            elif not st.session_state["draft_exercises"]:
                st.error("Thêm ít nhất 1 bài tập trước khi lưu.")
            else:
                save_key = DM.generate_id() if is_new else editing_key
                templates[save_key] = {"name": name.strip(), "exercises": st.session_state["draft_exercises"]}
                DM.save_workout_templates(templates)
                st.session_state["editing_template"] = None
                st.session_state["draft_exercises"] = []
                st.session_state.pop("draft_name", None)
                st.success("Đã lưu buổi tập.")
                st.rerun()
    with col_cancel:
        if st.button("❌ Hủy", use_container_width=True):
            st.session_state["editing_template"] = None
            st.session_state["draft_exercises"] = []
            st.session_state.pop("draft_name", None)
            st.rerun()

# ----------------------------------------------------------------------
# Mode 2: Quick-log a selected template
# ----------------------------------------------------------------------
elif st.session_state["selected_template"] is not None and st.session_state["selected_template"] in templates:
    selected_key = st.session_state["selected_template"]
    tpl = templates[selected_key]
    st.markdown(f"#### {tpl['name']}")
    if st.button("🔄 Chọn buổi tập khác"):
        st.session_state["selected_template"] = None
        st.rerun()

    DM.ensure_exercises_in_library(tpl["exercises"])
    workout_df = DM.load_workout_log()

    with st.form(f"template_form_{selected_key}", clear_on_submit=False):
        log_date = st.date_input("Ngày tập", value=date.today())
        rpe = st.slider("RPE chung cho buổi này", min_value=1, max_value=10, value=7)
        st.caption("Để cân nặng = 0 cho bài nào bạn không tập hôm nay — bài đó sẽ không được log.")
        st.divider()

        weight_inputs = {}
        for i, ex in enumerate(tpl["exercises"]):
            c1, c2, c3, c4 = st.columns([2.2, 1, 1, 1.2])
            with c1:
                st.markdown(f"**{ex['exercise_name']}**")
                st.caption(f"{ex['muscle_group']} · target {ex['sets']}x{ex['reps_display']}")
            with c2:
                sets_val = st.number_input("Sets", min_value=0, step=1, value=ex["sets"], key=f"tpl_{selected_key}_{i}_sets")
            with c3:
                reps_val = st.number_input("Reps", min_value=0, step=1, value=ex["reps_default"], key=f"tpl_{selected_key}_{i}_reps")
            with c4:
                weight_val = st.number_input("Kg", min_value=0.0, step=0.5, value=0.0, key=f"tpl_{selected_key}_{i}_weight")
            weight_inputs[i] = (sets_val, reps_val, weight_val)

        submitted = st.form_submit_button("✅ Lưu toàn bộ buổi tập", use_container_width=True)

        if submitted:
            entries = []
            for i, ex in enumerate(tpl["exercises"]):
                sets_val, reps_val, weight_val = weight_inputs[i]
                if weight_val <= 0:
                    continue
                entries.append((log_date, ex["muscle_group"], ex["exercise_name"], sets_val, reps_val, weight_val, rpe, ""))

            if not entries:
                st.warning("Chưa nhập cân nặng cho bài nào — không có gì được log.")
            else:
                batch_result = WA.log_workout_entries_batch(entries, workout_df=workout_df)
                logged_count = len(entries)
                total_xp = batch_result["xp_result"]["amount_awarded"]
                all_prs = [
                    f"{r['exercise']} ({', '.join(r['broken_prs'])})"
                    for r in batch_result["per_exercise"] if r["broken_prs"]
                ]

                st.success(f"Đã log {logged_count} bài tập (+{total_xp} XP).")
                if all_prs:
                    st.balloons()
                    st.success(f"🏆 PR mới: {', '.join(all_prs)}")
                if batch_result["xp_result"]["leveled_up"]:
                    st.success(f"🎉 LÊN CẤP! Bạn đang ở Level {RPG.load_rpg_state()['level']}")

                unlocked = WA.post_log_achievements_check()
                for ach in unlocked:
                    st.success(f"🏅 Mở khóa thành tích: {ach['name']}!")

                st.rerun()

# ----------------------------------------------------------------------
# Mode 3: List all templates (default view)
# ----------------------------------------------------------------------
else:
    if st.button("➕ Tạo buổi tập mới", use_container_width=True):
        st.session_state["editing_template"] = "__new__"
        st.session_state["draft_exercises"] = []
        st.session_state.pop("draft_name", None)
        st.rerun()

    st.write("")

    if not templates:
        st.info("Chưa có buổi tập nào — bấm nút trên để tạo buổi đầu tiên.")
    for key, tpl in templates.items():
        with st.container():
            st.markdown(f"#### {tpl['name']}")
            preview = ", ".join(f"{e['exercise_name']} ({e['sets']}x{e['reps_display']})" for e in tpl["exercises"])
            st.caption(preview)

            b1, b2, b3 = st.columns(3)
            with b1:
                if st.button("▶️ Chọn", key=f"pick_{key}", use_container_width=True):
                    st.session_state["selected_template"] = key
                    st.rerun()
            with b2:
                if st.button("✏️ Sửa", key=f"edit_{key}", use_container_width=True):
                    st.session_state["editing_template"] = key
                    st.session_state["draft_exercises"] = list(tpl["exercises"])
                    st.session_state["draft_name"] = tpl["name"]
                    st.rerun()
            with b3:
                if st.session_state["confirm_delete"] == key:
                    if st.button("⚠️ Bấm lại để xóa", key=f"confirm_del_{key}", use_container_width=True):
                        del templates[key]
                        DM.save_workout_templates(templates)
                        st.session_state["confirm_delete"] = None
                        st.rerun()
                else:
                    if st.button("🗑️ Xóa", key=f"del_{key}", use_container_width=True):
                        st.session_state["confirm_delete"] = key
                        st.rerun()
            st.divider()

bottom_tab_bar(active="more")
