import streamlit as st


def show_settings_page():
    """
    FraudTwin Settings Page
    """

    st.markdown(
        """
        <style>

        .settings-header {
            margin-bottom: 25px;
        }

        .settings-title {
            font-size: 32px;
            font-weight: 700;
            color: var(--ft-text, #F5F3F7);
            margin-bottom: 5px;
        }

        .settings-subtitle {
            color: var(--ft-muted, #AAA3B5);
            font-size: 14px;
        }

        .settings-card {
            background: var(--ft-surface, rgba(20, 17, 30, 0.90));
            border: 1px solid rgba(155, 77, 255, 0.20);
            border-radius: 14px;
            padding: 24px;
            margin-bottom: 20px;
        }

        .settings-card-title {
            color: var(--ft-text, #F5F3F7);
            font-size: 19px;
            font-weight: 650;
            margin-bottom: 5px;
        }

        .settings-card-description {
            color: var(--ft-muted, #AAA3B5);
            font-size: 13px;
            margin-bottom: 20px;
        }

        .profile-avatar {
            width: 75px;
            height: 75px;
            border-radius: 50%;
            background: linear-gradient(
                135deg,
                #8B3FF2,
                #C04CFF
            );
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 28px;
            font-weight: 700;
            margin-bottom: 15px;
        }

        .profile-name {
            color: var(--ft-text, #F5F3F7);
            font-size: 20px;
            font-weight: 650;
        }

        .profile-role {
            color: var(--ft-muted, #AAA3B5);
            font-size: 13px;
            margin-top: 3px;
        }

        </style>
        """,
        unsafe_allow_html=True,
    )

    # ---------------------------------------------------------
    # HEADER
    # ---------------------------------------------------------

    st.markdown(
        '<div class="settings-header">'
        '<div class="settings-title">Settings</div>'
        '<div class="settings-subtitle">Manage your FraudTwin account and application preferences.</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    # ---------------------------------------------------------
    # TABS
    # ---------------------------------------------------------

    profile_tab, preferences_tab, security_tab, about_tab = st.tabs(
        [
            "Profile",
            "Preferences",
            "Security",
            "About",
        ]
    )

    # =========================================================
    # PROFILE
    # =========================================================

    with profile_tab:

        st.markdown(
            '<div class="settings-card">'
            '<div class="settings-card-title">Profile</div>'
            '<div class="settings-card-description">Manage your FraudTwin account information.</div>'
            '</div>',
            unsafe_allow_html=True,
        )

        username = st.session_state.get(
            "username",
            "User",
        )

        current_role = st.session_state.get("role", "Fraud Analyst")

        col1, col2 = st.columns([1, 2])

        with col1:

            initials = username[:1].upper() if username else "U"

            st.markdown(
                f'<div class="profile-avatar">{initials}</div>'
                f'<div class="profile-name">{username}</div>'
                f'<div class="profile-role">{current_role}</div>',
                unsafe_allow_html=True,
            )

        with col2:

            full_name = st.text_input(
                "Full Name",
                value=st.session_state.get(
                    "full_name",
                    username,
                ),
                key="settings_full_name",
            )

            email = st.text_input(
                "Email",
                value=st.session_state.get(
                    "email",
                    "",
                ),
                placeholder="Enter your email",
                key="settings_email",
            )

            role_options = [
                "Fraud Analyst",
                "Risk Analyst",
                "Investigator",
                "Administrator",
            ]

            role_index = (
                role_options.index(current_role)
                if current_role in role_options
                else 0
            )

            role = st.selectbox(
                "Role",
                role_options,
                index=role_index,
                key="settings_role",
            )

            if st.button(
                "Save Profile",
                type="primary",
                use_container_width=True,
            ):

                st.session_state.full_name = full_name
                st.session_state.email = email
                st.session_state.role = role

                st.success(
                    "Profile updated successfully."
                )
                st.rerun()

    # =========================================================
    # PREFERENCES
    # =========================================================

    with preferences_tab:

        st.markdown(
            '<div class="settings-card">'
            '<div class="settings-card-title">Application Preferences</div>'
            '<div class="settings-card-description">Customize how FraudTwin behaves for you.</div>'
            '</div>',
            unsafe_allow_html=True,
        )

        appearance_options = ["Dark", "Light", "System Default"]
        risk_view_options = ["Risk Score", "Risk Level", "Investigation Priority"]

        saved_appearance = st.session_state.get("appearance", "Dark")
        appearance_index = (
            appearance_options.index(saved_appearance)
            if saved_appearance in appearance_options
            else 0
        )

        appearance = st.selectbox(
            "Appearance",
            appearance_options,
            index=appearance_index,
            key="settings_appearance",
            help="Dark and Light apply immediately. System Default currently renders as Dark.",
        )

        notifications = st.toggle(
            "Enable Notifications",
            value=st.session_state.get("notifications", True),
            key="settings_notifications",
        )

        saved_risk_view = st.session_state.get("risk_view", "Risk Score")
        risk_view_index = (
            risk_view_options.index(saved_risk_view)
            if saved_risk_view in risk_view_options
            else 0
        )

        risk_view = st.selectbox(
            "Default Risk View",
            risk_view_options,
            index=risk_view_index,
            key="settings_risk_view",
        )

        if st.button(
            "Save Preferences",
            type="primary",
            use_container_width=True,
        ):

            st.session_state.appearance = appearance
            st.session_state.notifications = notifications
            st.session_state.risk_view = risk_view

            st.success(
                "Preferences saved."
            )

            # FIX: inject_css() runs once at the top of route_page(), before
            # this button's click is handled, so without a rerun the new
            # appearance would only take visual effect on the *next*
            # interaction (e.g. clicking a sidebar link) instead of
            # immediately after hitting Save.
            st.rerun()

    # =========================================================
    # SECURITY
    # =========================================================

    with security_tab:

        st.markdown(
            '<div class="settings-card">'
            '<div class="settings-card-title">Security</div>'
            '<div class="settings-card-description">Manage your account security.</div>'
            '</div>',
            unsafe_allow_html=True,
        )

        st.subheader("Change Password")

        current_password = st.text_input(
            "Current Password",
            type="password",
            key="settings_current_password",
        )

        new_password = st.text_input(
            "New Password",
            type="password",
            key="settings_new_password",
        )

        confirm_password = st.text_input(
            "Confirm New Password",
            type="password",
            key="settings_confirm_password",
        )

        if st.button(
            "Update Password",
            use_container_width=True,
        ):

            if not current_password:
                st.error(
                    "Enter your current password."
                )

            elif not new_password:
                st.error(
                    "Enter a new password."
                )

            elif new_password != confirm_password:
                st.error(
                    "New passwords do not match."
                )

            else:
                st.success(
                    "Password updated successfully."
                )

                del st.session_state["settings_current_password"]
                del st.session_state["settings_new_password"]
                del st.session_state["settings_confirm_password"]
                st.rerun()

        st.divider()

        st.subheader("Session")

        st.write(
            "You are currently signed in as:",
            username,
        )

        if st.button(
            "Log Out",
            use_container_width=True,
            key="settings_log_out",
        ):

            st.session_state.authenticated = False
            st.session_state.username = ""
            st.session_state.page = "landing"
            st.session_state.confirm_logout = False

            st.rerun()

    # =========================================================
    # ABOUT
    # =========================================================

    with about_tab:

        st.markdown(
            '<div class="settings-card">'
            '<div class="settings-card-title">About FraudTwin</div>'
            '<div class="settings-card-description">Transaction risk analysis and fraud investigation, in one place.</div>'
            '</div>',
            unsafe_allow_html=True,
        )

        col1, col2 = st.columns(2)

        with col1:

            st.metric(
                "Version",
                "1.0.0",
            )

            st.metric(
                "Platform",
                "Fraud Intelligence",
            )

        with col2:

            st.metric(
                "Framework",
                "Streamlit",
            )

            st.metric(
                "AI / ML",
                "Enabled",
            )

        st.divider()

        st.write(
            "FraudTwin pulls together model scores, the context behind "
            "them, rule testing, and a proper investigation workflow, so "
            "a flagged transaction never just sits there unexplained."
        )

        st.caption(
            "FraudTwin — fraud intelligence, explained"
        )