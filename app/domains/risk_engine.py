import joblib
import numpy as np
import pandas as pd
import shap
import streamlit as st

from .config import (
    FEATURE_NAMES,
    MAX_CONTEXT_POINTS,
    ML_WEIGHT,
    CONTEXT_WEIGHT,
    MODEL_PATH,
    SCALER_PATH,
)


V_FEATURES = np.zeros(28)


@st.cache_resource
def load_model_and_scaler():
    model = joblib.load(MODEL_PATH)
    scaler = joblib.load(SCALER_PATH)
    return model, scaler


@st.cache_resource
def load_explainer(_model):
    return shap.TreeExplainer(_model)


model, scaler = load_model_and_scaler()
explainer = load_explainer(model)


def scale_transaction(hour, amount):
    time_seconds = hour * 3600
    scaled_values = scaler.transform(
        pd.DataFrame([[time_seconds, amount]], columns=["Time", "Amount"])
    )[0]
    return scaled_values[0], scaled_values[1]


def build_feature_row(scaled_time, scaled_amount):
    features = np.concatenate([[scaled_time], V_FEATURES, [scaled_amount]])
    return pd.DataFrame([features], columns=FEATURE_NAMES)


def compute_contextual_risk(hour, amount, device, location, transaction_type):
    points = 0
    factors = []

    if amount >= 100000:
        points += 10
        factors.append("Very high transaction amount detected")
    elif amount >= 50000:
        points += 8
        factors.append("High transaction amount detected")
    elif amount >= 25000:
        points += 5
        factors.append("Elevated transaction amount detected")

    if device == "New Device":
        points += 8
        factors.append("New device detected")

    if location == "Unusual Location":
        points += 8
        factors.append("Unusual transaction location")

    if transaction_type == "Online Purchase":
        points += 3
        factors.append("Online purchase context")
    elif transaction_type == "Large Transfer":
        points += 5
        factors.append("Large transfer context")

    if hour <= 5:
        points += 6
        factors.append("Unusual overnight transaction time")

    score = min(points, MAX_CONTEXT_POINTS)

    if not factors:
        factors.append("No additional contextual risk indicators detected")

    return score, factors


def combine_scores(ml_score, context_score):
    final = (
        ml_score * ML_WEIGHT
        + (context_score / MAX_CONTEXT_POINTS * 100) * CONTEXT_WEIGHT
    )
    return min(max(final, 0), 100)


def classify_risk(final_score):
    if final_score >= 70:
        return "HIGH RISK", "HIGH", "BLOCK / INVESTIGATE"
    elif final_score >= 30:
        return "MEDIUM RISK", "MEDIUM", "VERIFY / AUTHENTICATE"
    else:
        return "LOW RISK", "LOW", "APPROVE"


def generate_risk_controls(risk_score, attack_score=None, attack_indicators=0):
    controls = []

    if risk_score >= 70:
        controls += [
            "Block the transaction",
            "Initiate fraud investigation",
            "Require strong step-up authentication",
            "Verify the customer's device",
            "Verify transaction location",
        ]
    elif risk_score >= 30:
        controls += [
            "Require additional authentication",
            "Verify device ownership",
            "Request customer confirmation",
            "Increase transaction monitoring",
        ]
    else:
        controls += [
            "Approve the transaction",
            "Continue standard monitoring",
        ]

    if attack_score is not None:
        if attack_score >= 70:
            controls.append(
                "Escalate simulated attack for immediate investigation"
            )
        elif attack_score >= 50:
            controls.append("Apply enhanced transaction verification")

        if attack_indicators >= 3:
            controls.append(
                "Investigate multiple simultaneous risk indicators"
            )

    unique_controls = []
    for control in controls:
        if control not in unique_controls:
            unique_controls.append(control)

    return unique_controls


def score_transaction(hour, amount, device, location, transaction_type):
    scaled_time, scaled_amount = scale_transaction(hour, amount)
    input_df = build_feature_row(scaled_time, scaled_amount)

    probability = model.predict_proba(input_df)[0][1]
    ml_score = probability * 100

    context_score, factors = compute_contextual_risk(
        hour,
        amount,
        device,
        location,
        transaction_type,
    )

    final_score = combine_scores(ml_score, context_score)
    level, icon, decision = classify_risk(final_score)

    return {
        "amount": amount,
        "hour": hour,
        "device": device,
        "location": location,
        "type": transaction_type,
        "probability": probability,
        "ml_score": ml_score,
        "context_score": context_score,
        "factors": factors,
        "final_score": final_score,
        "level": level,
        "icon": icon,
        "decision": decision,
        "input_df": input_df,
    }


def calculate_attack_stress_score(original_result, attack_result):
    original_context = original_result["context_score"]
    attack_context = attack_result["context_score"]
    context_increase = max(attack_context - original_context, 0)

    attack_indicators = 0

    if attack_result["amount"] > original_result["amount"]:
        attack_indicators += 1

    if attack_result["hour"] != original_result["hour"]:
        attack_indicators += 1

    if (
        attack_result["device"] != original_result["device"]
        and attack_result["device"] == "New Device"
    ):
        attack_indicators += 1

    if (
        attack_result["location"] != original_result["location"]
        and attack_result["location"] == "Unusual Location"
    ):
        attack_indicators += 1

    if (
        attack_result["type"] != original_result["type"]
        and attack_result["type"] == "Large Transfer"
    ):
        attack_indicators += 1

    context_component = (attack_context / MAX_CONTEXT_POINTS) * 60
    attack_change_component = min(context_increase * 1.5, 25)
    indicator_component = min(attack_indicators * 4, 20)

    stress_score = (
        context_component
        + attack_change_component
        + indicator_component
    )

    if attack_indicators >= 4:
        stress_score = max(stress_score, 70)
    elif attack_indicators >= 3:
        stress_score = max(stress_score, 60)
    elif attack_indicators >= 2:
        stress_score = max(stress_score, 45)

    stress_score = min(max(float(stress_score), 0.0), 100.0)

    if stress_score >= 70:
        severity, severity_icon, attack_decision = (
            "SEVERE ATTACK",
            "SEVERE",
            "BLOCK / INVESTIGATE",
        )
    elif stress_score >= 50:
        severity, severity_icon, attack_decision = (
            "HIGH ATTACK RISK",
            "HIGH",
            "STEP-UP AUTHENTICATION",
        )
    elif stress_score >= 30:
        severity, severity_icon, attack_decision = (
            "MODERATE ATTACK RISK",
            "MODERATE",
            "VERIFY TRANSACTION",
        )
    else:
        severity, severity_icon, attack_decision = (
            "LOW ATTACK IMPACT",
            "LOW",
            "MONITOR",
        )

    return {
        "stress_score": stress_score,
        "attack_indicators": attack_indicators,
        "severity": severity,
        "severity_icon": severity_icon,
        "attack_decision": attack_decision,
        "context_increase": context_increase,
    }
