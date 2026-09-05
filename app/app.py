import sys
from pathlib import Path

import streamlit as st


# ============================================================
# MAKE APP DIRECTORY IMPORTABLE
# ============================================================

APP_DIR = Path(__file__).resolve().parent.parent

if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))


# ============================================================
# FRAUDTWIN — DOMAIN IMPORTS
# ============================================================

from domains.config import NAV_PAGES
from domains.state import initialize_state
from domains.ui import inject_css, risk_badge_html

from domains.home import page_home
from domains.analysis import page_transaction_analysis
from domains.investigation import page_investigation_center
from domains.reports import page_reports


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="FraudTwin",
    page_icon="FT",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# SESSION STATE
# ============================================================

initialize_state()


# ============================================================
# MAIN — NAVIGATION SHELL
# ============================================================

def main():
    inject_css()

    with st.sidebar:
        st.markdown(
            "<div class='ft-side-brand'> FraudTwin</div>",
            unsafe_allow_html=True
        )

        st.markdown(
            "<div class='ft-side-sub'>AI-Powered Transaction Risk Intelligence</div>",
            unsafe_allow_html=True
        )

        st.markdown(
            "<div class='ft-side-label'>Navigation</div>",
            unsafe_allow_html=True
        )

        current_page = st.session_state.page

        for index, nav_item in enumerate(NAV_PAGES):
            if st.button(
                nav_item,
                key=f"sidebar_nav_{index}",
                type=(
                    "primary"
                    if nav_item == current_page
                    else "secondary"
                ),
                width="stretch",
            ):
                if st.session_state.page != nav_item:
                    st.session_state.page = nav_item
                    st.rerun()

        st.markdown(
            "<div class='ft-side-divider'></div>",
            unsafe_allow_html=True
        )

        if (
            st.session_state.analyzed
            and st.session_state.analysis_data
        ):
            d = st.session_state.analysis_data

            st.markdown(
                "<div class='ft-side-current'>",
                unsafe_allow_html=True
            )

            st.markdown(
                "<div class='ft-side-current-label'>CURRENT TRANSACTION</div>",
                unsafe_allow_html=True
            )

            st.markdown(
                risk_badge_html(
                    d["level"],
                    d["icon"]
                ),
                unsafe_allow_html=True
            )

            st.markdown(
                f"<div class='ft-side-current-value'>₹{d['amount']:,.2f}</div>",
                unsafe_allow_html=True
            )

            st.markdown(
                f"<div style='color:#AAA3B5 !important;font-size:11.5px;margin-top:5px;'>Transaction time · {d['hour']:02d}:00</div>",
                unsafe_allow_html=True
            )

            st.markdown(
                "</div>",
                unsafe_allow_html=True
            )

            st.markdown(
                "<div class='ft-side-divider'></div>",
                unsafe_allow_html=True
            )

        st.markdown(
            "<div style='color:#AAA3B5;font-size:11.5px;line-height:1.6;'>Analyze transactions · Investigate alerts · Review reports</div>",
            unsafe_allow_html=True
        )

    page = st.session_state.page

    if page == "Home":
        page_home()

    elif page == "Analyze":
        page_transaction_analysis()

    elif page == "Investigate":
        page_investigation_center()

    elif page == "Reports":
        page_reports()


# ============================================================
# RUN APPLICATION
# ============================================================

if __name__ == "__main__":
    main()