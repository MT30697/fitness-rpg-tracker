"""Exercise Library - manage the user's custom exercise list."""
from __future__ import annotations

import streamlit as st

from components.ui import page_header
from utils import constants as C
from utils import data_manager as DM

page_header("Exercise Library", "📚", "Create and manage the exercises you train.")

library_df = DM.load_exercise_library()

# ----------------------------------------------------------------------
# Add new exercise
# ----------------------------------------------------------------------
with st.expander("➕ Add New Exercise", expanded=library_df.empty):
    with st.form("add_exercise_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Exercise Name")
            muscle_group = st.selectbox("Muscle Group", C.MUSCLE_GROUPS)
        with col2:
            equipment = st.selectbox("Equipment", C.EQUIPMENT_TYPES)
            notes = st.text_input("Notes (optional)")
        submitted = st.form_submit_button("Add Exercise", use_container_width=True)

        if submitted:
            if not name.strip():
                st.error("Exercise name is required.")
            else:
                row = {
                    "exercise_id": DM.generate_id(),
                    "exercise_name": name.strip(),
                    "muscle_group": muscle_group,
                    "equipment": equipment,
                    "notes": notes.strip(),
                    "created_at": DM.now_iso(),
                }
                DM.append_csv_row(C.EXERCISE_LIBRARY_FILE, row, C.EXERCISE_LIBRARY_COLUMNS)
                st.success(f"Added **{name}** to your library.")
                st.rerun()

st.divider()

# ----------------------------------------------------------------------
# Filters
# ----------------------------------------------------------------------
library_df = DM.load_exercise_library()

if library_df.empty:
    st.info("Your exercise library is empty. Add your first exercise above.")
else:
    f1, f2, f3 = st.columns(3)
    with f1:
        muscle_filter = st.multiselect("Filter by Muscle Group", C.MUSCLE_GROUPS)
    with f2:
        equip_filter = st.multiselect("Filter by Equipment", C.EQUIPMENT_TYPES)
    with f3:
        search = st.text_input("Search by name")

    filtered = library_df.copy()
    if muscle_filter:
        filtered = filtered[filtered["muscle_group"].isin(muscle_filter)]
    if equip_filter:
        filtered = filtered[filtered["equipment"].isin(equip_filter)]
    if search:
        filtered = filtered[filtered["exercise_name"].str.contains(search, case=False, na=False)]

    st.markdown(f"#### Exercises ({len(filtered)})")

    if filtered.empty:
        st.warning("No exercises match your filters.")
    else:
        for _, row in filtered.iterrows():
            with st.container():
                cols = st.columns([3, 2, 2, 3, 1, 1])
                cols[0].markdown(f"**{row['exercise_name']}**")
                cols[1].markdown(row["muscle_group"])
                cols[2].markdown(row["equipment"])
                cols[3].markdown(f"<span style='color:rgba(245,245,245,0.55)'>{row['notes'] or ''}</span>", unsafe_allow_html=True)

                edit_key = f"edit_{row['exercise_id']}"
                delete_key = f"delete_{row['exercise_id']}"

                if cols[4].button("✏️", key=edit_key, help="Edit"):
                    st.session_state["editing_exercise_id"] = row["exercise_id"]
                if cols[5].button("🗑️", key=delete_key, help="Delete"):
                    DM.delete_csv_row(C.EXERCISE_LIBRARY_FILE, C.EXERCISE_LIBRARY_COLUMNS, "exercise_id", row["exercise_id"])
                    st.rerun()

                if st.session_state.get("editing_exercise_id") == row["exercise_id"]:
                    with st.form(f"edit_form_{row['exercise_id']}"):
                        new_name = st.text_input("Name", value=row["exercise_name"])
                        new_muscle = st.selectbox(
                            "Muscle Group", C.MUSCLE_GROUPS,
                            index=C.MUSCLE_GROUPS.index(row["muscle_group"]) if row["muscle_group"] in C.MUSCLE_GROUPS else 0,
                        )
                        new_equip = st.selectbox(
                            "Equipment", C.EQUIPMENT_TYPES,
                            index=C.EQUIPMENT_TYPES.index(row["equipment"]) if row["equipment"] in C.EQUIPMENT_TYPES else 0,
                        )
                        new_notes = st.text_input("Notes", value=row["notes"] or "")
                        save_col, cancel_col = st.columns(2)
                        save = save_col.form_submit_button("Save", use_container_width=True)
                        cancel = cancel_col.form_submit_button("Cancel", use_container_width=True)

                        if save:
                            DM.update_csv_row(
                                C.EXERCISE_LIBRARY_FILE, C.EXERCISE_LIBRARY_COLUMNS, "exercise_id", row["exercise_id"],
                                {
                                    "exercise_name": new_name.strip(),
                                    "muscle_group": new_muscle,
                                    "equipment": new_equip,
                                    "notes": new_notes.strip(),
                                },
                            )
                            st.session_state["editing_exercise_id"] = None
                            st.success("Exercise updated.")
                            st.rerun()
                        if cancel:
                            st.session_state["editing_exercise_id"] = None
                            st.rerun()
                st.markdown("<hr style='margin:4px 0; border-color:rgba(255,255,255,0.18);'>", unsafe_allow_html=True)
