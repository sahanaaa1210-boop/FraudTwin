import sys
from pathlib import Path

import streamlit as st


# ============================================================
# PATH SETUP
# ============================================================

APP_DIR = Path(__file__).resolve().parent.parent

if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))


# ============================================================
# STREAMLIT CONFIG
# ============================================================

st.set_page_config(
    page_title="FraudTwin",
    page_icon="FT",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# IMPORTS
# ============================================================

from domains.config import NAV_PAGES
from domains.state import initialize_state
from domains.ui import inject_css, risk_badge_html

from domains.auth import (
    initialize_auth,
    show_auth_page,
    perform_logout,
)

from domains.landing import show_landing_page

from domains.home import page_home
from domains.analysis import page_transaction_analysis
from domains.investigation import page_investigation_center
from domains.reports import page_reports

from domains import setting


# ============================================================
# LANDING PAGE
# ============================================================

def render_landing_page():

    show_landing_page()


# ============================================================
# AUTHENTICATION PAGE
# ============================================================

def render_auth_page():

    if st.button(
        "← Landing Page",
        key="back_to_landing_page",
    ):

        st.session_state.page = "landing"

        if "confirm_login" in st.session_state:
            st.session_state.confirm_login = False

        if "confirm_signup" in st.session_state:
            st.session_state.confirm_signup = False

        st.rerun()

    if st.session_state.get(
        "authenticated",
        False,
    ):

        st.session_state.page = "Home"
        st.rerun()

    show_auth_page()


# ============================================================
# SETTINGS
# ============================================================

def render_settings():

    setting.show_settings_page()


# ============================================================
# SIDEBAR
# ============================================================

def render_sidebar():

    with st.sidebar:

        st.markdown(
            '<div class="ft-side-brand">FraudTwin</div>'
            '<div class="ft-side-sub">AI-Powered Transaction Risk Intelligence</div>'
            '<div class="ft-side-label">Navigation</div>',
            unsafe_allow_html=True,
        )

        navigation_pages = list(NAV_PAGES)

        if "Settings" not in navigation_pages:
            navigation_pages.append("Settings")

        current_page = st.session_state.get(
            "page",
            "Home",
        )

        for index, nav_item in enumerate(
            navigation_pages
        ):

            is_current = (
                nav_item == current_page
            )

            if st.button(
                nav_item,
                key=f"sidebar_nav_{index}",
                type=(
                    "primary"
                    if is_current
                    else "secondary"
                ),
                width="stretch",
            ):

                st.session_state.page = nav_item
                st.session_state.confirm_logout = False

                st.rerun()

        st.markdown(
            "<div class='ft-side-divider'></div>",
            unsafe_allow_html=True,
        )

        if (
            st.session_state.get(
                "analyzed",
                False,
            )
            and st.session_state.get(
                "analysis_data"
            )
        ):

            data = st.session_state.analysis_data

            st.markdown(
                """
                <div class="ft-side-current">
                """,
                unsafe_allow_html=True,
            )

            st.markdown(
                """
                <div class="ft-side-current-label">
                    CURRENT TRANSACTION
                </div>
                """,
                unsafe_allow_html=True,
            )

            if (
                "level" in data
                and "icon" in data
            ):

                st.markdown(
                    risk_badge_html(
                        data["level"],
                        data["icon"],
                    ),
                    unsafe_allow_html=True,
                )

            if "amount" in data:

                st.markdown(
                    f"""
                    <div class="ft-side-current-value">
                        ₹{data["amount"]:,.2f}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            if "hour" in data:

                st.markdown(
                    f"""
                    <div style="
                        color:#AAA3B5 !important;
                        font-size:11.5px;
                        margin-top:5px;
                    ">
                        Transaction time ·
                        {data["hour"]:02d}:00
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            st.markdown(
                "</div>",
                unsafe_allow_html=True,
            )

            st.markdown(
                "<div class='ft-side-divider'></div>",
                unsafe_allow_html=True,
            )

        username = st.session_state.get(
            "username",
            "User",
        )

        st.markdown(
            f"""
            <div style="
                color:#AAA3B5;
                font-size:11.5px;
                line-height:1.6;
                margin-bottom:10px;
            ">
                Signed in as
                <strong style="color:#F5F3F7;">
                    {username}
                </strong>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button(
            "Log out",
            width="stretch",
            key="sidebar_logout",
        ):

            perform_logout()

        st.markdown(
            "<div class='ft-side-divider'></div>",
            unsafe_allow_html=True,
        )

        st.markdown(
            """
            <div style="
                color:#AAA3B5;
                font-size:11.5px;
                line-height:1.6;
            ">
                Analyze transactions · Investigate alerts ·
                Review reports
            </div>
            """,
            unsafe_allow_html=True,
        )


# ============================================================
# PAGE ROUTER
# ============================================================

def route_page():

    page = st.session_state.get(
        "page",
        "landing",
    )

    authenticated = st.session_state.get(
        "authenticated",
        False,
    )

    if page == "landing":

        if authenticated:

            st.session_state.page = "Home"
            st.rerun()

        render_landing_page()

        return

    if page == "auth":

        if authenticated:

            st.session_state.page = "Home"
            st.rerun()

        render_auth_page()

        return

    if not authenticated:

        st.session_state.page = "landing"

        st.rerun()

    # ========================================================
    # APPLICATION CSS
    # ========================================================
    # FIX: theme now comes from the "Appearance" preference saved on the
    # Settings page (Dark / Light / System Default) instead of always
    # rendering the hardcoded dark stylesheet. "System Default" falls
    # back to Dark since Streamlit has no reliable way to read the OS
    # theme from Python.

    appearance = st.session_state.get("appearance", "Dark")
    theme = appearance if appearance in ("Dark", "Light") else "Dark"

    inject_css(theme)

    render_sidebar()

    if page == "Home":

        page_home()

    elif page == "Analyze":

        page_transaction_analysis()

    elif page == "Investigate":

        page_investigation_center()

    elif page == "Reports":

        page_reports()

    elif page == "Settings":

        render_settings()

    elif page == "🏠 Home":

        page_home()

    elif page == "🔍 Analyze":

        page_transaction_analysis()

    elif page == "🕵️ Investigate":

        page_investigation_center()

    elif page == "📈 Reports":

        page_reports()

    else:

        st.session_state.page = "Home"

        st.rerun()


# ============================================================
# MAIN
# ============================================================

def main():

    initialize_auth()

    initialize_state()

    route_page()


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    main()