import streamlit as st

from .ai_manager import generate_ai_risk_assessment
from .ui import section_title, stat_card


def page_ai_risk_manager():
    section_title(
        " AI Risk Manager",
        "AI-generated, plain-language decision support — it never changes the ML score"
    )

    if (
        not st.session_state.analyzed
        or st.session_state.analysis_data is None
    ):
        st.info(
            "Analyze a transaction first on the **Analyze** page, "
            "then come back here."
        )
        return

    data = st.session_state.analysis_data
    attack_result = st.session_state.attack_result

    attack_score = (
        attack_result.get("stress_score")
        if attack_result
        else None
    )

    attack_indicators = (
        attack_result.get("attack_indicators", 0)
        if attack_result
        else 0
    )

    c1, c2, c3 = st.columns(3)

    with c1:
        stat_card(
            f"{data['final_score']:.0f}/100",
            "Current Risk Score"
        )

    with c2:
        stat_card(
            data["decision"],
            "Current Decision"
        )

    with c3:
        stat_card(
            f"{attack_score:.0f}/100"
            if attack_score is not None
            else "—",
            "Attack Stress Score"
        )

    st.markdown(
        "<div style='height:10px;'></div>",
        unsafe_allow_html=True
    )

    st.info(
        "This is decision support for a human risk manager — "
        "it does not replace or modify the FraudTwin Risk Intelligence Score."
    )

    if st.button(
        " Generate AI Risk Assessment",
        type="primary",
        width="stretch",
        key="generate_ai_assessment"
    ):
        try:
            with st.spinner(
                "AI Risk Manager is analyzing the transaction..."
            ):
                st.session_state.ai_result = (
                    generate_ai_risk_assessment(
                        amount=data["amount"],
                        transaction_hour=data["hour"],
                        device=data["device"],
                        location=data["location"],
                        transaction_type=data["type"],
                        ml_probability=data["probability"],
                        context_score=data["context_score"],
                        final_risk_score=data["final_score"],
                        risk_level=data["level"],
                        decision=data["decision"],
                        contextual_factors=data["factors"],
                        attack_score=attack_score,
                        attack_indicators=attack_indicators
                    )
                )

        except Exception as e:
            st.session_state.ai_result = None
            st.error(
                "The AI Risk Manager could not generate an assessment."
            )
            st.caption(
                f"Technical detail: {str(e)}"
            )

    if st.session_state.ai_result:
        st.markdown(
            "<div class='ft-divider'></div>",
            unsafe_allow_html=True
        )

        st.success(
            "AI Risk Assessment generated successfully."
        )

        st.markdown(
            st.session_state.ai_result
        )