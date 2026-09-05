from datetime import datetime

import pandas as pd
import streamlit as st

from .state import go_to
from .ui import section_title

def _live_risk_monitor_body():
    """Render a compact live activity panel from persisted FraudTwin history."""
    history = st.session_state.risk_history
    now = datetime.now()

    if history:
        latest = history[-1]
        scores = [float(x.get("Risk Score", 0)) for x in history]
        avg = sum(scores) / len(scores) if scores else 0
        elevated = sum(1 for x in history if float(x.get("Risk Score", 0)) >= 50)
        latest_level = str(latest.get("Risk Level", "UNKNOWN"))
        latest_score = float(latest.get("Risk Score", 0))
        latest_amount = float(latest.get("Amount", 0))
        latest_time = latest.get("Transaction Time", "—")
        latest_device = latest.get("Device", "—")
        latest_location = latest.get("Location", "—")
        latest_decision = latest.get("Decision", "—")
    else:
        avg = 0
        elevated = 0
        latest_level = "WAITING"
        latest_score = 0
        latest_amount = 0
        latest_time = "—"
        latest_device = "—"
        latest_location = "—"
        latest_decision = "Awaiting first transaction"

    status_class = "live-good" if latest_score < 50 else "live-alert"
    st.markdown(
        f"""
        <div class="ft-live-panel">
            <div class="ft-live-header">
                <div>
                    <div class="ft-live-title">Live Risk Monitor</div>
                    <div class="ft-live-sub">Real-time transaction activity and risk signals</div>
                </div>
                <div class="ft-live-status"><span class="ft-live-dot"></span> LIVE · {now.strftime('%d %b %Y · %H:%M:%S')}</div>
            </div>
            <div class="ft-live-grid">
                <div class="ft-live-metric"><span>Transactions Monitored</span><strong>{len(history)}</strong></div>
                <div class="ft-live-metric"><span>Average Risk</span><strong>{avg:.0f}/100</strong></div>
                <div class="ft-live-metric"><span>Elevated Alerts</span><strong>{elevated}</strong></div>
                <div class="ft-live-metric"><span>Active Investigations</span><strong>{sum(1 for x in st.session_state.investigation_history if x.get('Status') not in ('Resolved - Legitimate', 'Resolved - Fraud'))}</strong></div>
            </div>
            <div class="ft-live-latest">
                <div class="ft-live-latest-label">LATEST TRANSACTION SIGNAL</div>
                <div class="ft-live-latest-main">₹{latest_amount:,.2f} · {latest_time} · <span class="{status_class}">{latest_level} · {latest_score:.2f}/100</span></div>
                <div class="ft-live-latest-sub">{latest_device} · {latest_location} · Decision: <b>{latest_decision}</b></div>
            </div>
        </div>
        """, unsafe_allow_html=True
    )


# Streamlit 1.37+ supports fragments with periodic reruns. Use them when available
# so the monitor visibly refreshes without refreshing the whole application.
if hasattr(st, "fragment"):
    live_risk_monitor = st.fragment(run_every="5s")(_live_risk_monitor_body)
else:
    live_risk_monitor = _live_risk_monitor_body


# ============================================================
# PAGE: HOME
# ============================================================

def page_home():
    # Compact product hero: the Home page introduces the product without
    # pushing the useful content below the fold.
    st.markdown(
        """
        <div class="ft-hero">
            <div class="ft-eyebrow">AI-Powered Fraud Intelligence</div>
            <div class="ft-hero-title"> FraudTwin</div>
            <div class="ft-hero-sub">
                Score transactions, understand the signals behind the decision,
                stress-test suspicious activity, and move from alert to action —
                all in one risk intelligence workspace.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Live operational surface: keeps Home useful even before another navigation action.
    live_risk_monitor()
    st.markdown("<div style='height:18px;'></div>", unsafe_allow_html=True)

    # Primary actions stay immediately visible and are deliberately ranked.
    c1, c2, c3 = st.columns([1.15, 1, 1])
    with c1:
        if st.button("Start Analysis", type="primary", width="stretch", key="home_start_analysis"):
            go_to("Analyze")
            st.rerun()
    with c2:
        if st.button("Open Investigation", width="stretch", key="home_open_investigation"):
            go_to("Investigate")
            st.rerun()
    with c3:
        if st.button("View Reports", width="stretch", key="home_view_reports"):
            go_to("Reports")
            st.rerun()

    st.markdown("<div class='ft-home-section'>", unsafe_allow_html=True)
    section_title("What FraudTwin does", "Six capabilities working together across the transaction lifecycle")

    capabilities = [
        ("01", "Risk Scoring", "Combines the trained ML model with transaction context to produce one clear risk score."),
        ("02", "Explainable AI", "Shows the signals that pushed the score up or down, so the decision is easier to trust."),
        ("03", "What-If Simulation", "Change amount, device or location and see how the risk profile shifts."),
        ("04", "Attack Simulator", "Stress-test a transaction against common fraud patterns before they happen for real."),
        ("05", "Investigation Workspace", "Turn alerts into trackable cases with notes, status and an audit trail."),
        ("06", "AI Risk Manager", "Get a plain-language recommendation from Gemini based on the detected signals."),
    ]

    cols = st.columns(3)
    for i, (icon, title, text) in enumerate(capabilities):
        with cols[i % 3]:
            st.markdown(
                f"""<div class="ft-home-cap-card">
                        <div class="ft-home-cap-icon">{icon}</div>
                        <div class="ft-home-cap-title">{title}</div>
                        <div class="ft-home-cap-text">{text}</div>
                    </div>""",
                unsafe_allow_html=True
            )
            st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='ft-divider'></div>", unsafe_allow_html=True)
    section_title("How a transaction moves through FraudTwin", "From raw transaction to a clear, reviewable action")
    st.markdown(
        """
        <div class="ft-home-flow">
            <span class="ft-home-step"><b>1</b> Transaction</span>
            <span class="ft-home-arrow">→</span>
            <span class="ft-home-step"><b>2</b> Risk Analysis</span>
            <span class="ft-home-arrow">→</span>
            <span class="ft-home-step"><b>3</b> Suspicious Indicators</span>
            <span class="ft-home-arrow">→</span>
            <span class="ft-home-step"><b>4</b> AI Explanation</span>
            <span class="ft-home-arrow">→</span>
            <span class="ft-home-step"><b>5</b> Investigation</span>
            <span class="ft-home-arrow">→</span>
            <span class="ft-home-step"><b>6</b> Recommended Action</span>
        </div>
        <div class="ft-home-note">The goal is simple: turn a suspicious transaction into an understandable decision.</div>
        """,
        unsafe_allow_html=True
    )


# ============================================================
