import streamlit as st

from .config import NAV_PAGES
from .storage import (
    load_persistent_history,
    load_investigation_history,
    persist_active_case,
)


# ============================================================
# FRAUDTWIN — SESSION STATE
# ============================================================


def _init_state(key, default):
    if key not in st.session_state:
        st.session_state[key] = default


def initialize_state():
    _init_state("page", NAV_PAGES[0])
    _init_state("analyzed", False)
    _init_state("analysis_data", None)
    _init_state("twin_result", None)
    _init_state("attack_result", None)
    _init_state("ai_result", None)
    _init_state(
        "risk_history",
        load_persistent_history()
    )
    _init_state(
        "investigation_history",
        load_investigation_history()
    )
    _init_state("investigation_case", None)
    _init_state("investigation_status", "Open")
    _init_state("investigation_notes", "")


def go_to(page_name):
    st.session_state.page = page_name


def sync_investigation_status():
    current_status = (
        st.session_state.investigation_status_selector
    )

    st.session_state.investigation_status = current_status

    if st.session_state.investigation_case is not None:

        st.session_state.investigation_case["Status"] = (
            current_status
        )

        st.session_state.investigation_case["Notes"] = (
            st.session_state.get(
                "investigation_notes_input",
                st.session_state.investigation_notes
            )
        )

        st.session_state.investigation_notes = (
            st.session_state.investigation_case["Notes"]
        )

        persist_active_case()


def mark_case_under_review():
    st.session_state.investigation_status = "Under Review"

    if st.session_state.investigation_case is not None:

        st.session_state.investigation_case["Status"] = (
            "Under Review"
        )

        st.session_state.investigation_case["Notes"] = (
            st.session_state.get(
                "investigation_notes_input",
                st.session_state.investigation_notes
            )
        )

        st.session_state.investigation_notes = (
            st.session_state.investigation_case["Notes"]
        )

        persist_active_case()


def resolve_case():
    st.session_state.investigation_status = (
        "Resolved - Legitimate"
    )

    if st.session_state.investigation_case is not None:

        st.session_state.investigation_case["Status"] = (
            "Resolved - Legitimate"
        )

        st.session_state.investigation_case["Notes"] = (
            st.session_state.get(
                "investigation_notes_input",
                st.session_state.investigation_notes
            )
        )

        st.session_state.investigation_notes = (
            st.session_state.investigation_case["Notes"]
        )

        persist_active_case()