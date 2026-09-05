import numpy as np
import pandas as pd
import streamlit as st

from .ai_manager import generate_ai_risk_assessment
from .config import (
    DEVICE_OPTIONS,
    FEATURE_NAMES,
    LOCATION_OPTIONS,
    MAX_CONTEXT_POINTS,
    TYPE_OPTIONS,
)
from .risk_engine import (
    calculate_attack_stress_score,
    explainer,
    score_transaction,
)
from .state import go_to
from .storage import add_to_risk_history
from .ui import (
    ft_bar_chart,
    indicator_row,
    risk_badge_html,
    score_hero,
    section_title,
    stat_card,
)

def render_transaction_form():
    section_title("Enter Transaction Details", "Fill in the details below, then run the analysis")

    # Reset an old invalid widget state once so the form opens with a usable demo value.
    if "original_amount" in st.session_state and float(st.session_state.original_amount) < 1.0:
        st.session_state.original_amount = 5000.0

    c1, c2 = st.columns([1, 1], gap="medium")
    with c1:
        amount = st.number_input(
            "Transaction Amount (₹)",
            min_value=1.0,
            value=5000.0,
            step=100.0,
            key="original_amount",
        )
    with c2:
        transaction_hour = st.slider(
            "Transaction Hour",
            min_value=0,
            max_value=23,
            value=14,
            key="original_hour",
        )

    c1, c2, c3 = st.columns([1, 1, 1], gap="medium")
    with c1:
        device = st.selectbox("Device", DEVICE_OPTIONS, key="original_device")
    with c2:
        location = st.selectbox("Location", LOCATION_OPTIONS, key="original_location")
    with c3:
        transaction_type = st.selectbox("Transaction Type", TYPE_OPTIONS, key="original_type")

    if st.button("Analyze Transaction", type="primary", width="stretch"):
        result = score_transaction(transaction_hour, amount, device, location, transaction_type)
        st.session_state.analysis_data = result
        st.session_state.analyzed = True
        st.session_state.twin_result = None
        st.session_state.attack_result = None
        st.session_state.ai_result = None
        add_to_risk_history(result)
        st.rerun()


def render_result_overview(data):
    score_hero(data["final_score"], data["level"], data["icon"], data["decision"])

    c1, c2, c3 = st.columns(3)
    with c1: stat_card(f"{data['probability']*100:.1f}%", "ML Fraud Probability")
    with c2: stat_card(f"{data['context_score']:.0f}/30", "Context Risk")
    with c3: stat_card(f"₹{data['amount']:,.0f}", "Amount")

    st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)
    section_title("Why this score?", "Key indicators found in this transaction")
    for factor in data["factors"]:
        indicator_row(factor)

    with st.expander("Score breakdown & model drivers"):
        breakdown_df = pd.DataFrame({
            "Component": ["ML Fraud Probability", "Context Contribution"],
            "Score": [data["ml_score"], data["context_score"] / MAX_CONTEXT_POINTS * 100]
        }).set_index("Component")
        ft_bar_chart(breakdown_df, "Score", "Risk Contribution (0–100)")

        st.write(
            "SHAP explains how the trained machine-learning model influenced the "
            "ML fraud prediction. Time and Amount are the live model features used "
            "in this demonstration."
        )
        try:
            shap_values = explainer.shap_values(data["input_df"])
            if isinstance(shap_values, list):
                shap_row = np.asarray(shap_values[-1])[0]
            else:
                shap_array = np.asarray(shap_values)
                if shap_array.ndim == 3:
                    shap_row = shap_array[0, :, -1]
                elif shap_array.ndim == 2:
                    shap_row = shap_array[0]
                else:
                    shap_row = shap_array
            shap_row = np.asarray(shap_row).flatten()

            if len(shap_row) == len(FEATURE_NAMES):
                explanation_df = pd.DataFrame({
                    "Feature": FEATURE_NAMES,
                    "SHAP Impact": shap_row,
                    "Absolute Impact": np.abs(shap_row)
                }).sort_values("Absolute Impact", ascending=False)

                top_features = explanation_df.head(8)
                st.subheader("Top Model Drivers")
                for _, row in top_features.iterrows():
                    feature, impact = row["Feature"], row["SHAP Impact"]
                    if impact > 0:
                        st.write(f" **{feature}** — increased fraud prediction (impact: +{impact:.4f})")
                    elif impact < 0:
                        st.write(f" **{feature}** — reduced fraud prediction (impact: {impact:.4f})")
                    else:
                        st.write(f"⚪ **{feature}** — minimal effect")

                chart_df = top_features[["Feature", "SHAP Impact"]].set_index("Feature")
                ft_bar_chart(chart_df, "SHAP Impact", "SHAP Impact")
        except Exception as e:
            st.warning("SHAP explanation could not be generated.")
            st.caption(f"Technical detail: {str(e)}")

    with st.expander(" Technical model details"):
        st.write("The trained XGBoost model expects 30 features: Time, V1–V28 and Amount.")
        st.dataframe(data["input_df"], width="stretch")
        st.caption(
            "V1–V28 are anonymized PCA-based features from the original credit-card "
            "fraud dataset and are not derivable from a live transaction in this demo, "
            "so they are held at zero. Device, Location and Transaction Type are "
            "evaluated separately through contextual risk rules."
        )


def render_twin_tab(data):
    st.write("Create a hypothetical version of this transaction and see how the risk assessment changes.")

    amount, transaction_hour = data["amount"], data["hour"]
    device, location, transaction_type = data["device"], data["location"], data["type"]

    c1, c2 = st.columns(2)
    with c1:
        twin_amount = st.number_input("Twin Amount (₹)", min_value=1.0, value=float(amount), step=100.0, key="twin_amount")
        twin_device = st.selectbox("Twin Device", DEVICE_OPTIONS, index=DEVICE_OPTIONS.index(device), key="twin_device")
        twin_type = st.selectbox("Twin Transaction Type", TYPE_OPTIONS, index=TYPE_OPTIONS.index(transaction_type), key="twin_type")
    with c2:
        twin_hour = st.slider("Twin Transaction Hour", min_value=0, max_value=23, value=int(transaction_hour), key="twin_hour")
        twin_location = st.selectbox("Twin Location", LOCATION_OPTIONS, index=LOCATION_OPTIONS.index(location), key="twin_location")

    if st.button(" Run FraudTwin Simulation", width="stretch", key="run_twin"):
        twin = score_transaction(twin_hour, twin_amount, twin_device, twin_location, twin_type)
        twin["ml_change"] = twin["ml_score"] - data["ml_score"]
        twin["final_change"] = twin["final_score"] - data["final_score"]
        st.session_state.twin_result = twin
        st.rerun()

    twin = st.session_state.twin_result
    if twin is None:
        return

    st.markdown("<div class='ft-divider'></div>", unsafe_allow_html=True)
    section_title("Original vs Twin")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("** Original Transaction**")
        st.metric("Risk Intelligence Score", f"{data['final_score']:.2f}/100")
        st.markdown(risk_badge_html(data["level"], data["icon"]), unsafe_allow_html=True)
        st.caption(f"₹{amount:,.2f} · {transaction_hour:02d}:00 · {device} · {location} · {transaction_type}")
    with c2:
        st.markdown("** Twin Transaction**")
        st.metric("Risk Intelligence Score", f"{twin['final_score']:.2f}/100", delta=f"{twin['final_change']:+.2f}")
        st.markdown(risk_badge_html(twin["level"], twin["icon"]), unsafe_allow_html=True)
        st.caption(f"₹{twin['amount']:,.2f} · {twin['hour']:02d}:00 · {twin['device']} · {twin['location']} · {twin['type']}")

    chart_df = pd.DataFrame({"Scenario": ["Original", "Twin"], "Risk Score": [data["final_score"], twin["final_score"]]}).set_index("Scenario")
    ft_bar_chart(chart_df, "Risk Score", "Risk Intelligence Score (0–100)")

    section_title(" What changed?")
    changes = []
    if amount != twin["amount"]: changes.append(f" Amount: ₹{amount:,.2f} → ₹{twin['amount']:,.2f}")
    if transaction_hour != twin["hour"]: changes.append(f" Time: {transaction_hour:02d}:00 → {twin['hour']:02d}:00")
    if device != twin["device"]: changes.append(f" Device: {device} → {twin['device']}")
    if location != twin["location"]: changes.append(f" Location: {location} → {twin['location']}")
    if transaction_type != twin["type"]: changes.append(f" Type: {transaction_type} → {twin['type']}")
    if not changes: changes.append("No transaction values were changed.")
    for change in changes:
        indicator_row(change)

    if data["decision"] != twin["decision"]:
        st.warning(f"⚠ Recommended action changed from **{data['decision']}** to **{twin['decision']}**.")
    else:
        st.info(f"ℹ Recommended action remains **{twin['decision']}**.")


def render_attack_tab(data):
    st.write("Stress-test this transaction against common fraud attack patterns. The real ML prediction is preserved — the Attack Stress Score is a separate rule-based stress test.")

    amount, transaction_hour = data["amount"], data["hour"]
    device, location, transaction_type = data["device"], data["location"], data["type"]

    attack_scenarios = {
        " High Amount Attack": {
            "description": "Simulates a sudden high-value transaction.",
            "amount": max(float(amount) * 10, 50000.0), "hour": int(transaction_hour),
            "device": device, "location": location, "type": transaction_type,
        },
        " New Device Attack": {
            "description": "Simulates a transaction from a previously unseen device.",
            "amount": float(amount), "hour": int(transaction_hour),
            "device": "New Device", "location": location, "type": transaction_type,
        },
        " Unusual Location Attack": {
            "description": "Simulates a transaction from an unusual location.",
            "amount": float(amount), "hour": int(transaction_hour),
            "device": device, "location": "Unusual Location", "type": transaction_type,
        },
        " Midnight Transaction": {
            "description": "Simulates a transaction during unusual overnight hours.",
            "amount": float(amount), "hour": 2,
            "device": device, "location": location, "type": transaction_type,
        },
        " Combined Fraud Attack": {
            "description": "Simulates a coordinated attack: high amount, new device, unusual location, midnight timing, large transfer.",
            "amount": max(float(amount) * 10, 50000.0), "hour": 2,
            "device": "New Device", "location": "Unusual Location", "type": "Large Transfer",
        },
    }

    selected_attack = st.selectbox(" Select an Attack Scenario", list(attack_scenarios.keys()), key="attack_scenario")
    attack = attack_scenarios[selected_attack]
    st.info(f"**{selected_attack}** — {attack['description']}")

    if st.button(" Simulate Attack Scenario", width="stretch", key="simulate_attack"):
        attack_result = score_transaction(attack["hour"], attack["amount"], attack["device"], attack["location"], attack["type"])
        attack_result["ml_change"] = attack_result["ml_score"] - data["ml_score"]
        attack_result["standard_final_change"] = attack_result["final_score"] - data["final_score"]
        attack_result["scenario"] = selected_attack
        attack_result["description"] = attack["description"]

        attack_stress = calculate_attack_stress_score(
            {"amount": amount, "hour": transaction_hour, "device": device, "location": location,
             "type": transaction_type, "context_score": data["context_score"], "final_score": data["final_score"]},
            attack_result
        )
        attack_result.update(attack_stress)
        st.session_state.attack_result = attack_result
        st.rerun()

    attack_result = st.session_state.attack_result
    if attack_result is None:
        return

    st.markdown("<div class='ft-divider'></div>", unsafe_allow_html=True)
    section_title("Original vs Attack Scenario")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("** Original Transaction**")
        st.metric("Risk Intelligence Score", f"{data['final_score']:.2f}/100")
        st.markdown(risk_badge_html(data["level"], data["icon"]), unsafe_allow_html=True)
    with c2:
        st.markdown(f"**{attack_result['scenario']}**")
        st.metric("ML-Based Risk Intelligence", f"{attack_result['final_score']:.2f}/100")
        st.caption(f"Context Risk: {attack_result['context_score']:.0f}/30")

    st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
    section_title(" Attack Stress Assessment", "A separate rule-based stress score — it does not change the ML model's fraud probability")

    c1, c2, c3 = st.columns(3)
    with c1: stat_card(f"{float(attack_result['stress_score']):.0f}/100", "Attack Stress Score")
    with c2: stat_card(attack_result["attack_indicators"], "Attack Indicators")
    with c3: stat_card(f"{attack_result['context_score']}/30", "Context Risk")

    st.markdown(risk_badge_html(attack_result["severity"], attack_result["severity_icon"]), unsafe_allow_html=True)
    st.progress(min(max(int(attack_result["stress_score"]), 0), 100))

    if attack_result["stress_score"] >= 70:
        st.error(" **BLOCK / INVESTIGATE** — Multiple suspicious attack characteristics were detected.")
    elif attack_result["stress_score"] >= 50:
        st.warning("**STEP-UP AUTHENTICATION** — The simulated attack presents significant risk characteristics.")
    elif attack_result["stress_score"] >= 30:
        st.warning(" **VERIFY TRANSACTION** — The simulated scenario introduces additional risk indicators.")
    else:
        st.success(" **MONITOR** — The simulated attack produced limited additional risk indicators.")

    comparison_df = pd.DataFrame({
        "Metric": ["Original Risk Intelligence", "Attack ML-Based Risk", "Attack Stress Score"],
        "Score": [data["final_score"], attack_result["final_score"], attack_result["stress_score"]]
    }).set_index("Metric")
    ft_bar_chart(comparison_df, "Score", "Score (0–100)")

    section_title("Attack indicators detected")
    attack_changes = []
    if amount != attack_result["amount"]: attack_changes.append(f" Amount changed: ₹{amount:,.2f} → ₹{attack_result['amount']:,.2f}")
    if transaction_hour != attack_result["hour"]: attack_changes.append(f" Time changed: {transaction_hour:02d}:00 → {attack_result['hour']:02d}:00")
    if device != attack_result["device"]: attack_changes.append(f" Device changed: {device} → {attack_result['device']}")
    if location != attack_result["location"]: attack_changes.append(f" Location changed: {location} → {attack_result['location']}")
    if transaction_type != attack_result["type"]: attack_changes.append(f" Type changed: {transaction_type} → {attack_result['type']}")
    if not attack_changes:
        indicator_row("No attack characteristics were introduced.", positive=True)
    else:
        for change in attack_changes:
            indicator_row(change)

    with st.expander(" Why can ML Probability and Attack Stress Score differ?"):
        st.write(
            "The trained ML model produces the actual fraud probability from its "
            "available model features. The Attack Stress Score is a separate "
            "rule-based simulation layer designed to evaluate hypothetical attack "
            "characteristics — so a hypothetical attack can have a lower ML "
            "probability while still receiving a high Attack Stress Score."
        )


def page_transaction_analysis():
    section_title("Analyze", "Score a transaction, understand the risk, and test what-if scenarios")
    render_transaction_form()

    if not st.session_state.analyzed or st.session_state.analysis_data is None:
        st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
        st.info("Enter a transaction above and click **Analyze Transaction** to see the risk assessment.")
        return

    data = st.session_state.analysis_data
    st.markdown("<div class='ft-divider'></div>", unsafe_allow_html=True)

    # Keep the workflow visible without creating more pages.
    n1, n2, n3 = st.columns([1, 1, 1])
    with n1:
        st.markdown("**1 · Risk Assessment**")
    with n2:
        st.markdown("**2 · What-If / Attack**")
    with n3:
        if st.button(" Continue to Investigation", width="stretch", key="analysis_to_investigation"):
            go_to("Investigate")
            st.rerun()

    tab1, tab2, tab3 = st.tabs([" Risk Assessment", " What-If Twin", " Attack Simulator"])
    with tab1:
        render_result_overview(data)
    with tab2:
        render_twin_tab(data)
    with tab3:
        render_attack_tab(data)

    st.markdown("<div class='ft-divider'></div>", unsafe_allow_html=True)
    with st.expander(" AI Risk Manager", expanded=False):
        st.caption("Optional decision support. It uses the existing FraudTwin scores and never changes them.")
        if st.button("Generate AI Risk Assessment", type="primary", width="stretch", key="analyze_page_ai"):
            try:
                attack_result = st.session_state.attack_result
                attack_score = attack_result.get("stress_score") if attack_result else None
                attack_indicators = attack_result.get("attack_indicators", 0) if attack_result else 0
                with st.spinner("AI Risk Manager is analyzing the transaction..."):
                    st.session_state.ai_result = generate_ai_risk_assessment(
                        amount=data["amount"], transaction_hour=data["hour"], device=data["device"],
                        location=data["location"], transaction_type=data["type"],
                        ml_probability=data["probability"], context_score=data["context_score"],
                        final_risk_score=data["final_score"], risk_level=data["level"], decision=data["decision"],
                        contextual_factors=data["factors"], attack_score=attack_score,
                        attack_indicators=attack_indicators
                    )
            except Exception as e:
                st.session_state.ai_result = None
                st.error("The AI Risk Manager could not generate an assessment.")
                st.caption(f"Technical detail: {str(e)}")

        if st.session_state.ai_result:
            st.success("AI Risk Assessment generated successfully.")
            st.markdown(st.session_state.ai_result)
