from datetime import datetime

import pandas as pd
import streamlit as st

from .risk_engine import generate_risk_controls
from .state import (
    go_to,
    mark_case_under_review,
    resolve_case,
    sync_investigation_status,
)
from .storage import save_investigation_history
from .ui import indicator_row, section_title, stat_card

def page_investigation_center():
    section_title("Investigate", "Review the alert, record findings, and track the case to resolution")
    if st.button("← Back to Analyze", width="content", key="investigation_back"):
        go_to("Analyze")
        st.rerun()

    if not st.session_state.analyzed or st.session_state.analysis_data is None:
        st.info("Analyze a transaction first on the **Analyze** page, then come back here.")
        return

    data = st.session_state.analysis_data
    attack_result = st.session_state.attack_result
    attack_score = attack_result.get("stress_score") if attack_result else None
    attack_indicators = attack_result.get("attack_indicators", 0) if attack_result else 0

    investigation_score = data["final_score"]
    if attack_score is not None:
        investigation_score = max(investigation_score, attack_score)

    if investigation_score >= 70:
        alert_priority, alert_message = " CRITICAL", "Immediate investigation recommended — high-risk characteristics detected."
    elif investigation_score >= 50:
        alert_priority, alert_message = " HIGH", "Enhanced investigation recommended — multiple suspicious characteristics."
    elif investigation_score >= 30:
        alert_priority, alert_message = " MEDIUM", "Review recommended before final transaction approval."
    else:
        alert_priority, alert_message = " LOW", "No immediate investigation escalation is required."

    c1, c2, c3 = st.columns(3)
    with c1: stat_card(alert_priority, "Alert Priority")
    with c2: stat_card(f"{investigation_score:.0f}/100", "Investigation Score")
    with c3: stat_card(st.session_state.investigation_status, "Case Status")

    if investigation_score >= 70: st.error(f" {alert_message}")
    elif investigation_score >= 50: st.warning(f"{alert_message}")
    elif investigation_score >= 30: st.warning(f" {alert_message}")
    else: st.success(f" {alert_message}")

    st.markdown("<div class='ft-divider'></div>", unsafe_allow_html=True)
    section_title(" Alert Details")
    c1, c2 = st.columns(2)
    with c1:
        st.write(f"**Amount:** ₹{data['amount']:,.2f}")
        st.write(f"**Time:** {data['hour']:02d}:00")
        st.write(f"**Risk Level:** {data['icon']} {data['level']}")
        st.write(f"**Recommended Decision:** {data['decision']}")
    with c2:
        st.write(f"**Device:** {data['device']}")
        st.write(f"**Location:** {data['location']}")
        st.write(f"**Transaction Type:** {data['type']}")
        st.write(f"**Attack Stress Score:** {f'{attack_score:.2f}/100' if attack_score is not None else 'No attack simulation run'}")

    section_title("Investigation Triggers")
    triggers = []
    if data["final_score"] >= 70: triggers.append(" High transaction risk score")
    elif data["final_score"] >= 30: triggers.append(" Medium transaction risk score")
    if data["device"] == "New Device": triggers.append(" New device detected")
    if data["location"] == "Unusual Location": triggers.append(" Unusual transaction location")
    if data["hour"] <= 5: triggers.append(" Overnight transaction")
    if data["amount"] >= 50000: triggers.append(" High-value transaction")
    if attack_score is not None and attack_score >= 50: triggers.append(" Significant simulated attack stress")
    if attack_indicators >= 3: triggers.append(" Multiple attack indicators detected")
    if not triggers: triggers.append(" No major investigation triggers detected")
    for trigger in triggers:
        indicator_row(trigger)

    controls = generate_risk_controls(data["final_score"], attack_score, attack_indicators)
    section_title(" Recommended Risk Controls")
    for control in controls:
        indicator_row(control)

    st.markdown("<div class='ft-divider'></div>", unsafe_allow_html=True)
    section_title(" Case Management")

    c1, c2 = st.columns(2)
    status_options = ["Open", "Under Review", "Escalated", "Resolved - Fraud", "Resolved - Legitimate"]

    # Keep the widget state synchronized BEFORE the selectbox is created.
    # This avoids Streamlit's WidgetAlreadyInstantiatedError when a button
    # callback changes the investigation status.
    if st.session_state.get("investigation_status_selector") != st.session_state.investigation_status:
        st.session_state.investigation_status_selector = st.session_state.investigation_status

    with c1:
        st.selectbox("Investigation Status", status_options, key="investigation_status_selector", on_change=sync_investigation_status)
    with c2:
        st.text_area(
            "Analyst Investigation Notes", value=st.session_state.investigation_notes,
            placeholder="Record why the alert was investigated, what was verified, and what action was taken.",
            key="investigation_notes_input"
        )
    st.session_state.investigation_notes = st.session_state.investigation_notes_input

    a1, a2, a3 = st.columns(3)
    with a1:
        if st.button(" Create Investigation Case", width="stretch", key="create_investigation_case"):
            case_id = "FT-" + datetime.now().strftime("%Y%m%d%H%M%S")
            current_status = st.session_state.investigation_status_selector
            st.session_state.investigation_status = current_status
            st.session_state.investigation_notes = st.session_state.get("investigation_notes_input", st.session_state.investigation_notes)
            st.session_state.investigation_case = {
                "Case ID": case_id, "Created": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Amount": float(data["amount"]), "Risk Score": float(data["final_score"]),
                "Alert Priority": alert_priority, "Status": current_status,
                "Decision": data["decision"], "Notes": st.session_state.investigation_notes,
            }
            st.session_state.investigation_history.append(dict(st.session_state.investigation_case))
            save_investigation_history()
            st.success(f" Investigation case **{case_id}** created and saved permanently.")
    with a2:
        if st.button(" Mark Under Review", width="stretch", key="mark_under_review", on_click=mark_case_under_review):
            st.success(" Case status updated to Under Review.")
    with a3:
        if st.button(" Resolve Alert", width="stretch", key="resolve_alert", on_click=resolve_case):
            st.success(" Alert marked as resolved.")

    if st.session_state.investigation_case is not None:
        st.session_state.investigation_case["Status"] = st.session_state.investigation_status
        st.session_state.investigation_case["Notes"] = st.session_state.investigation_notes
        section_title(" Active Investigation Case")
        st.dataframe(pd.DataFrame([st.session_state.investigation_case]), width="stretch", hide_index=True)
