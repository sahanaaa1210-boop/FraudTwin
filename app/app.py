import streamlit as st
import pandas as pd
import json
import numpy as np
import joblib
import shap
import altair as alt
import time
from pathlib import Path
from datetime import datetime
from google import genai


# ============================================================
# FRAUDTWIN — AI-Powered Transaction Risk Intelligence
# ============================================================

st.set_page_config(
    page_title="FraudTwin",
    page_icon="FT",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_PATH = BASE_DIR / "models" / "fraud_model.pkl"
SCALER_PATH = BASE_DIR / "models" / "scaler.pkl"
DATA_DIR = BASE_DIR / "data"
HISTORY_FILE = DATA_DIR / "transaction_history.csv"
INVESTIGATION_FILE = DATA_DIR / "investigation_cases.json"


# ============================================================
# MODEL LOADING (unchanged)
# ============================================================

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


# ============================================================
# CONSTANTS
# ============================================================

FEATURE_NAMES = ["Time", *[f"V{i}" for i in range(1, 29)], "Amount"]
V_FEATURES = np.zeros(28)

DEVICE_OPTIONS = ["Trusted Device", "New Device"]
LOCATION_OPTIONS = ["Usual Location", "Unusual Location"]
TYPE_OPTIONS = ["Normal Purchase", "Online Purchase", "Large Transfer"]

ML_WEIGHT = 0.80
CONTEXT_WEIGHT = 0.20
MAX_CONTEXT_POINTS = 30

NAV_PAGES = [
    "Home",
    "Analyze",
    "Investigate",
    "Reports",
]

RISK_COLORS = {
    "HIGH RISK": "#E05260",
    "MEDIUM RISK": "#D6A84F",
    "LOW RISK": "#45A56A",
    "SEVERE ATTACK": "#E05260",
    "HIGH ATTACK RISK": "#E05260",
    "MODERATE ATTACK RISK": "#D6A84F",
    "LOW ATTACK IMPACT": "#45A56A",
}


# ============================================================
# SESSION STATE
# ============================================================

def _init_state(key, default):
    if key not in st.session_state:
        st.session_state[key] = default


def load_persistent_history():
    try:
        if HISTORY_FILE.exists():
            df = pd.read_csv(HISTORY_FILE)
            if not df.empty:
                return df.to_dict("records")
    except Exception:
        pass
    return []


def load_investigation_history():
    try:
        if INVESTIGATION_FILE.exists():
            with INVESTIGATION_FILE.open("r", encoding="utf-8") as file:
                data = json.load(file)
                if isinstance(data, list):
                    return data
    except Exception:
        pass
    return []


def save_investigation_history():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with INVESTIGATION_FILE.open("w", encoding="utf-8") as file:
        json.dump(
            st.session_state.investigation_history,
            file, indent=2, ensure_ascii=False, default=str
        )


def save_risk_history():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if st.session_state.risk_history:
        pd.DataFrame(st.session_state.risk_history).to_csv(HISTORY_FILE, index=False)
    else:
        pd.DataFrame().to_csv(HISTORY_FILE, index=False)


_init_state("page", NAV_PAGES[0])
_init_state("analyzed", False)
_init_state("analysis_data", None)
_init_state("twin_result", None)
_init_state("attack_result", None)
_init_state("ai_result", None)
_init_state("risk_history", load_persistent_history())
_init_state("investigation_history", load_investigation_history())
_init_state("investigation_case", None)
_init_state("investigation_status", "Open")
_init_state("investigation_notes", "")


def go_to(page_name):
    st.session_state.page = page_name


# ============================================================
# CORE RISK ENGINE (unchanged logic)
# ============================================================

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
        controls += ["Approve the transaction", "Continue standard monitoring"]

    if attack_score is not None:
        if attack_score >= 70:
            controls.append("Escalate simulated attack for immediate investigation")
        elif attack_score >= 50:
            controls.append("Apply enhanced transaction verification")
        if attack_indicators >= 3:
            controls.append("Investigate multiple simultaneous risk indicators")

    unique_controls = []
    for control in controls:
        if control not in unique_controls:
            unique_controls.append(control)
    return unique_controls


def generate_ai_risk_assessment(
    amount, transaction_hour, device, location, transaction_type,
    ml_probability, context_score, final_risk_score, risk_level, decision,
    contextual_factors, attack_score=None, attack_indicators=0
):
    """
    Use Gemini as decision-support for the existing FraudTwin risk engine.
    The ML Risk Intelligence Score is never changed by the AI.
    """
    api_key = st.secrets.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY was not found in .streamlit/secrets.toml.")

    client = genai.Client(api_key=api_key)

    factors_text = (
        "\n".join(f"- {factor}" for factor in contextual_factors)
        if contextual_factors else "- No contextual risk factors detected"
    )

    if attack_score is None:
        attack_text = "No attack simulation has been run."
    else:
        attack_text = (
            f"Attack Stress Score: {attack_score:.2f}/100\n"
            f"Attack indicators: {attack_indicators}"
        )

    prompt = f"""
You are the AI Risk Manager inside FraudTwin, an AI-powered transaction risk intelligence system.

Your job is to interpret the deterministic ML and contextual risk results and provide concise decision support for a human risk manager.
Do NOT change, override, or recalculate the FraudTwin Risk Intelligence Score. Do NOT invent facts that are not provided.
The AI recommendation must be based only on the transaction information and risk signals below.

TRANSACTION
- Amount: INR {amount:,.2f}
- Time: {transaction_hour:02d}:00
- Device: {device}
- Location: {location}
- Transaction Type: {transaction_type}

FRAUDTWIN RISK SIGNALS
- ML Fraud Probability: {ml_probability * 100:.2f}%
- Context Risk: {context_score:.0f}/30
- Risk Intelligence Score: {final_risk_score:.2f}/100
- Risk Level: {risk_level}
- Existing Recommended Decision: {decision}

CONTEXTUAL RISK FACTORS
{factors_text}

ATTACK SIMULATION
{attack_text}

Return the answer using exactly these six headings:

### AI Risk Assessment
Give a 2-3 sentence interpretation of the overall risk.

### Key Risk Factors
Give 3-5 concise bullet points using only the supplied evidence.

### AI Recommended Decision
State one action: APPROVE, VERIFY / AUTHENTICATE, or BLOCK / INVESTIGATE. Briefly explain why.

### Recommended Risk Controls
Give 3-5 practical controls appropriate to the risk.

### Investigation Priority
Choose LOW, MEDIUM, HIGH, or CRITICAL and explain the priority in one sentence.

### AI Reasoning
Give a short explanation connecting the ML score, contextual risk, and attack signals (if present) to the recommendation.

This is decision support, not a replacement for the human risk manager.
"""

    configured_model = st.secrets.get("GEMINI_MODEL", "gemini-3.7-flash")
    model_candidates = []
    for candidate in [configured_model, "gemini-3.7-flash", "gemini-3.6-flash", "gemini-3.5-flash-lite"]:
        if candidate and candidate not in model_candidates:
            model_candidates.append(candidate)

    last_error = None
    for model_name in model_candidates:
        for attempt in range(2):
            try:
                response = client.models.generate_content(model=model_name, contents=prompt)
                if response is None or not getattr(response, "text", None):
                    raise ValueError(f"Gemini returned an empty response from {model_name}.")
                return response.text.strip()
            except Exception as error:
                last_error = error
                error_text = str(error).lower()
                temporary_error = any(
                    marker in error_text for marker in
                    ["503", "unavailable", "high demand", "temporarily",
                     "deadline exceeded", "internal server error"]
                )
                if not temporary_error:
                    break
                if attempt == 0:
                    time.sleep(3)

    raise RuntimeError(
        "Gemini is temporarily unavailable. The AI Risk Manager tried "
        "multiple Gemini Flash models and retries, but none returned a "
        "response. Your FraudTwin ML risk assessment is still valid. "
        f"Last API error: {last_error}"
    )


def score_transaction(hour, amount, device, location, transaction_type):
    scaled_time, scaled_amount = scale_transaction(hour, amount)
    input_df = build_feature_row(scaled_time, scaled_amount)
    probability = model.predict_proba(input_df)[0][1]
    ml_score = probability * 100
    context_score, factors = compute_contextual_risk(hour, amount, device, location, transaction_type)
    final_score = combine_scores(ml_score, context_score)
    level, icon, decision = classify_risk(final_score)

    return {
        "amount": amount, "hour": hour, "device": device, "location": location,
        "type": transaction_type, "probability": probability, "ml_score": ml_score,
        "context_score": context_score, "factors": factors, "final_score": final_score,
        "level": level, "icon": icon, "decision": decision, "input_df": input_df,
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
    if attack_result["device"] != original_result["device"] and attack_result["device"] == "New Device":
        attack_indicators += 1
    if attack_result["location"] != original_result["location"] and attack_result["location"] == "Unusual Location":
        attack_indicators += 1
    if attack_result["type"] != original_result["type"] and attack_result["type"] == "Large Transfer":
        attack_indicators += 1

    context_component = (attack_context / MAX_CONTEXT_POINTS) * 60
    attack_change_component = min(context_increase * 1.5, 25)
    indicator_component = min(attack_indicators * 4, 20)
    stress_score = context_component + attack_change_component + indicator_component

    if attack_indicators >= 4:
        stress_score = max(stress_score, 70)
    elif attack_indicators >= 3:
        stress_score = max(stress_score, 60)
    elif attack_indicators >= 2:
        stress_score = max(stress_score, 45)

    stress_score = min(max(float(stress_score), 0.0), 100.0)

    if stress_score >= 70:
        severity, severity_icon, attack_decision = "SEVERE ATTACK", "SEVERE", "BLOCK / INVESTIGATE"
    elif stress_score >= 50:
        severity, severity_icon, attack_decision = "HIGH ATTACK RISK", "HIGH", "STEP-UP AUTHENTICATION"
    elif stress_score >= 30:
        severity, severity_icon, attack_decision = "MODERATE ATTACK RISK", "MODERATE", "VERIFY TRANSACTION"
    else:
        severity, severity_icon, attack_decision = "LOW ATTACK IMPACT", "LOW", "MONITOR"

    return {
        "stress_score": stress_score, "attack_indicators": attack_indicators,
        "severity": severity, "severity_icon": severity_icon,
        "attack_decision": attack_decision, "context_increase": context_increase,
    }


def add_to_risk_history(result):
    history_entry = {
        "Time Recorded": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Amount": result["amount"],
        "Transaction Time": f"{result['hour']:02d}:00",
        "Device": result["device"],
        "Location": result["location"],
        "Transaction Type": result["type"],
        "ML Probability": result["probability"] * 100,
        "Context Risk": result["context_score"],
        "Risk Score": result["final_score"],
        "Risk Level": result["level"],
        "Decision": result["decision"],
    }
    st.session_state.risk_history.append(history_entry)
    save_risk_history()


def persist_active_case():
    if st.session_state.investigation_case is None:
        return
    case_id = st.session_state.investigation_case["Case ID"]
    for index, case in enumerate(st.session_state.investigation_history):
        if case.get("Case ID") == case_id:
            st.session_state.investigation_history[index] = dict(st.session_state.investigation_case)
            save_investigation_history()
            return


def sync_investigation_status():
    current_status = st.session_state.investigation_status_selector
    st.session_state.investigation_status = current_status
    if st.session_state.investigation_case is not None:
        st.session_state.investigation_case["Status"] = current_status
        st.session_state.investigation_case["Notes"] = st.session_state.get(
            "investigation_notes_input", st.session_state.investigation_notes
        )
        st.session_state.investigation_notes = st.session_state.investigation_case["Notes"]
        persist_active_case()


def mark_case_under_review():
    st.session_state.investigation_status = "Under Review"
    if st.session_state.investigation_case is not None:
        st.session_state.investigation_case["Status"] = "Under Review"
        st.session_state.investigation_case["Notes"] = st.session_state.get(
            "investigation_notes_input", st.session_state.investigation_notes
        )
        st.session_state.investigation_notes = st.session_state.investigation_case["Notes"]
        persist_active_case()


def resolve_case():
    st.session_state.investigation_status = "Resolved - Legitimate"
    if st.session_state.investigation_case is not None:
        st.session_state.investigation_case["Status"] = "Resolved - Legitimate"
        st.session_state.investigation_case["Notes"] = st.session_state.get(
            "investigation_notes_input", st.session_state.investigation_notes
        )
        st.session_state.investigation_notes = st.session_state.investigation_case["Notes"]
        persist_active_case()


# ============================================================
# THEME / CSS
# ============================================================

def inject_css():
    st.markdown("""
    <style>
    :root {
        --ft-bg: #0B0A0F;
        --ft-sidebar: #111018;
        --ft-surface: #171522;
        --ft-surface-elevated: #211A2B;
        --ft-bronze: #542B72;
        --ft-accent: #9B4DFF;
        --ft-gold: #D8B5FF;
        --ft-magenta: #D946EF;
        --ft-text: #F5F3F7;
        --ft-muted: #AAA3B5;
        --ft-border: #30283A;
        --ft-success: #45A56A;
        --ft-error: #E05260;
        --ft-brand: #F5F3F7;
        --ft-canvas: #0B0A0F;
        --ft-body: #F5F3F7;
        --ft-white: #171522;
    }

    html, body, [data-testid="stAppViewContainer"], .stApp {
        overflow-x: hidden !important;
        background: #0B0A0F !important;
    }

    /* Rich pictorial background: abstract AI-fintech command center */
    [data-testid="stAppViewContainer"]::before {
        content: "";
        position: fixed;
        inset: 0;
        pointer-events: none;
        z-index: 0;
        opacity: 1;
        background:
            radial-gradient(ellipse 520px 330px at 86% 18%, rgba(155,77,255,0.20), transparent 68%),
            radial-gradient(ellipse 430px 300px at 72% 72%, rgba(217,70,239,0.13), transparent 70%),
            radial-gradient(ellipse 360px 260px at 12% 44%, rgba(84,43,114,0.16), transparent 72%),
            linear-gradient(rgba(196,181,253,0.035) 1px, transparent 1px),
            linear-gradient(90deg, rgba(196,181,253,0.035) 1px, transparent 1px);
        background-size: auto, auto, auto, 48px 48px, 48px 48px;
    }
    .main > div { position: relative; z-index: 1; }

    /* Decorative fintech network: charts, nodes, radar and data columns */
    .ft-background-art {
        position: fixed; right: -2vw; top: 7vh; width: 64vw; height: 68vh;
        pointer-events: none; z-index: 0; opacity: .62;
        transform: translateY(0);
    }
    .ft-background-art svg { width: 100%; height: 100%; overflow: visible; }
    .ft-art-grid { stroke: #30283A; stroke-width: 1; opacity: .65; }
    .ft-art-axis { stroke: #AAA3B5; stroke-width: 1; opacity: .18; }
    .ft-art-line { fill: none; stroke: url(#ftLine); stroke-width: 3; opacity: .72; }
    .ft-art-line-soft { fill: none; stroke: #542B72; stroke-width: 2; opacity: .48; }
    .ft-art-ring { fill: none; stroke: #9B4DFF; stroke-width: 1.5; opacity: .24; }
    .ft-art-bar { fill: #542B72; opacity: .42; }
    .ft-art-bar-bright { fill: #9B4DFF; opacity: .62; }
    .ft-art-label { fill: #AAA3B5; font-family: sans-serif; font-size: 10px; letter-spacing: 2px; opacity: .34; }
    .ft-art-panel { fill: #171522; stroke: #30283A; stroke-width: 1; opacity: .36; }
    .main > div { position: relative; z-index: 1; }
    [data-testid="stHeader"] {
        background: #0B0A0F !important;
    }
    [data-testid="stSidebar"] {
        background: #111018 !important;
        border-right: 1px solid #30283A !important;
    }
    [data-testid="stSidebar"] > div:first-child {
        background: #111018 !important;
    }
    [data-testid="stSidebar"] * {
        color: #F5F3F7 !important;
    }
    /* TRUE FULL-WIDTH WORKSPACE
       Streamlit versions use different wrappers for the main block.
       Target every known wrapper so collapsing the sidebar never leaves a
       centered 1200/1400px column surrounded by empty space. */
    [data-testid="stAppViewContainer"] .main,
    [data-testid="stAppViewContainer"] .main > div,
    [data-testid="stMain"],
    [data-testid="stMain"] > div,
    [data-testid="stMainBlockContainer"],
    [data-testid="stMain"] .block-container,
    .stMainBlockContainer,
    .block-container {
        width: 100% !important;
        max-width: none !important;
        min-width: 0 !important;
        margin-left: 0 !important;
        margin-right: 0 !important;
        box-sizing: border-box !important;
    }

    [data-testid="stMainBlockContainer"],
    [data-testid="stMain"] .block-container,
    .stMainBlockContainer,
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 3rem !important;
        padding-left: clamp(18px, 2vw, 36px) !important;
        padding-right: clamp(18px, 2vw, 36px) !important;
    }

    /* When the sidebar is collapsed, force the main content to occupy the
       entire viewport rather than retaining Streamlit's centered max width. */
    [data-testid="stSidebar"][aria-expanded="false"] ~ [data-testid="stMain"],
    [data-testid="stSidebar"][aria-expanded="false"] ~ [data-testid="stMain"] > div,
    [data-testid="stSidebar"][aria-expanded="false"] ~ [data-testid="stMain"] .block-container {
        width: 100vw !important;
        max-width: 100vw !important;
        margin-left: 0 !important;
        margin-right: 0 !important;
    }

    .ft-live-panel {
        background: linear-gradient(135deg, rgba(23,21,34,.96), rgba(33,26,43,.92));
        border: 1px solid rgba(155,77,255,.42); border-radius: 16px; padding: 20px 22px;
        box-shadow: 0 12px 35px rgba(0,0,0,.20), inset 0 1px 0 rgba(196,181,253,.06);
        position: relative; overflow: hidden;
    }
    .ft-live-panel::after {
        content:""; position:absolute; right:-80px; top:-120px; width:300px; height:300px;
        border-radius:50%; background:radial-gradient(circle, rgba(155,77,255,.14), transparent 68%); pointer-events:none;
    }
    .ft-live-header { display:flex; justify-content:space-between; align-items:flex-start; gap:20px; }
    .ft-live-title { font-size:20px; font-weight:800; color:#F5F3F7; }
    .ft-live-sub { margin-top:3px; font-size:12.5px; color:#AAA3B5; }
    .ft-live-status { white-space:nowrap; color:#6EE7A8; font-size:11px; font-weight:800; letter-spacing:.5px;
        border:1px solid rgba(110,231,168,.25); background:rgba(69,165,106,.10); padding:7px 10px; border-radius:999px; }
    .ft-live-dot { display:inline-block; width:7px; height:7px; border-radius:50%; background:#6EE7A8; margin-right:6px; box-shadow:0 0 10px rgba(110,231,168,.7); }
    .ft-live-grid { display:grid; grid-template-columns:repeat(4,1fr); gap:10px; margin-top:17px; }
    .ft-live-metric { background:rgba(11,10,15,.36); border:1px solid #30283A; border-radius:10px; padding:12px 14px; }
    .ft-live-metric span { display:block; color:#AAA3B5; font-size:11px; margin-bottom:4px; }
    .ft-live-metric strong { color:#F5F3F7; font-size:22px; }
    .ft-live-latest { margin-top:12px; border-top:1px solid #30283A; padding-top:13px; }
    .ft-live-latest-label { color:#AAA3B5; font-size:10px; font-weight:800; letter-spacing:1.2px; }
    .ft-live-latest-main { margin-top:5px; color:#F5F3F7; font-size:15px; font-weight:700; }
    .ft-live-latest-sub { margin-top:5px; color:#AAA3B5; font-size:12px; }
    .live-good { color:#6EE7A8; } .live-alert { color:#F3C86B; }
    @media (max-width: 900px) {
        .ft-live-grid { grid-template-columns:repeat(2,1fr); }
        .ft-live-header { flex-direction:column; }
    }

    h1, h2, h3, h4 { color: #F5F3F7 !important; font-weight: 700 !important; }
    p, li, span, label { color: #F5F3F7; }
    [data-testid="stMarkdownContainer"] p, [data-testid="stMarkdownContainer"] li { color: #F5F3F7 !important; }
    [data-testid="stMarkdownContainer"] h1, [data-testid="stMarkdownContainer"] h2, [data-testid="stMarkdownContainer"] h3 { color: #F5F3F7 !important; }
    small, .stCaption, [data-testid="stCaptionContainer"] { color: #AAA3B5 !important; }

    .ft-hero {
        position: relative;
        overflow: hidden;
        background: linear-gradient(135deg, rgba(23,21,34,0.98), rgba(33,26,43,0.96));
        border: 1px solid rgba(155,77,255,0.28);
        border-radius: 18px;
        padding: 30px 32px;
        margin-bottom: 20px;
        box-shadow: 0 18px 45px rgba(0,0,0,0.20);
    }
    .ft-hero::after {
        content: ""; position: absolute; width: 280px; height: 280px;
        right: -100px; top: -120px; border-radius: 50%;
        background: radial-gradient(circle, rgba(155,77,255,0.18), transparent 68%);
        pointer-events: none;
    }
    .ft-eyebrow {
        display: inline-block; font-size: 11px; letter-spacing: 1.5px;
        text-transform: uppercase; color: #C4B5FD; font-weight: 800;
        background: rgba(155,77,255,0.14); border: 1px solid rgba(155,77,255,0.24);
        padding: 6px 12px; border-radius: 999px; margin-bottom: 12px;
    }
    .ft-hero-title { font-size: 34px; font-weight: 800; color: #F5F3F7; margin: 0 0 8px 0; letter-spacing: -0.6px; }
    .ft-hero-sub { font-size: 15px; color: #AAA3B5; max-width: 760px; line-height: 1.55; margin: 0; }

    .ft-home-kicker { color:#AAA3B5; font-size:12px; text-transform:uppercase; letter-spacing:1.3px; font-weight:800; margin:0 0 7px 0; }
    .ft-home-section { margin-top: 28px; }
    .ft-home-cap-card {
        background: rgba(23,21,34,0.94); border:1px solid #30283A; border-radius:14px;
        padding:18px 19px; min-height:156px; transition:all .15s ease;
    }
    .ft-home-cap-card:hover { border-color:rgba(155,77,255,.55); transform:translateY(-2px); box-shadow:0 12px 28px rgba(0,0,0,.18); }
    .ft-home-cap-icon {
        display:inline-flex; align-items:center; justify-content:center;
        width:34px; height:34px; margin-bottom:10px;
        border-radius:9px; background:rgba(155,77,255,0.12);
        border:1px solid rgba(155,77,255,0.32);
        color:#C4B5FD; font-size:11px; font-weight:800;
        letter-spacing:.6px;
    }
    .ft-home-cap-title { font-size:15px; font-weight:800; color:#F5F3F7; margin-bottom:6px; }
    .ft-home-cap-text { font-size:12.8px; color:#AAA3B5; line-height:1.5; }
    .ft-home-flow {
        display:flex; align-items:center; gap:8px; flex-wrap:wrap; padding:17px 18px;
        background:rgba(23,21,34,.82); border:1px solid #30283A; border-radius:14px;
    }
    .ft-home-step {
        display:inline-flex; align-items:center; gap:7px; padding:8px 11px;
        border:1px solid rgba(196,181,253,.16); background:rgba(33,26,43,.72);
        border-radius:999px; color:#F5F3F7; font-size:12px; font-weight:700;
    }
    .ft-home-arrow { color:#AAA3B5; font-size:15px; }
    .ft-home-note { color:#AAA3B5; font-size:12px; margin-top:9px; }

    .ft-card {
        background: #171522;
        border: 1px solid #30283A;
        border-radius: 14px;
        padding: 22px 22px;
        height: 100%;
        transition: border-color 0.15s ease, transform 0.15s ease;
        box-shadow: 0 2px 10px rgba(44,30,26,0.04);
    }
    .ft-card:hover { border-color: #9B4DFF; transform: translateY(-2px); }
    .ft-card-icon { font-size: 26px; margin-bottom: 10px; }
    .ft-card-title { font-size: 16px; font-weight: 700; color: #F5F3F7; margin-bottom: 6px; }
    .ft-card-text { font-size: 13.5px; color: #AAA3B5; line-height: 1.55; }

    .ft-section-title { font-size: 22px; font-weight: 700; color: #F5F3F7; margin-bottom: 2px; }
    .ft-section-sub { font-size: 14px; color: #AAA3B5; margin-bottom: 18px; }

    .ft-badge {
        display: inline-flex; align-items: center; gap: 8px;
        padding: 6px 16px; border-radius: 999px; font-weight: 700; font-size: 14px;
        border: 1px solid #30283A;
    }
    .ft-score-wrap {
        display: flex; align-items: center; gap: 28px; flex-wrap: wrap;
        background: #171522; border: 1px solid #30283A;
        border-radius: 16px; padding: 26px 28px; margin-bottom: 18px;
        box-shadow: 0 2px 10px rgba(44,30,26,0.04);
    }
    .ft-score-number { font-size: 54px; font-weight: 800; line-height: 1; color: #F5F3F7; }
    .ft-score-label { font-size: 13px; color: #AAA3B5; text-transform: uppercase; letter-spacing: 1px; }

    .ft-status-marker {
        display:inline-flex; align-items:center; justify-content:center;
        min-width:42px; padding:3px 7px; border-radius:6px;
        background:rgba(155,77,255,.12); border:1px solid rgba(155,77,255,.25);
        color:#C4B5FD; font-size:9px; font-weight:800; letter-spacing:.7px;
    }

    .ft-indicator {
        display: flex; align-items: center; gap: 10px;
        background: #171522; border: 1px solid #30283A;
        border-radius: 10px; padding: 10px 14px; margin-bottom: 8px; font-size: 14px;
        color: #F5F3F7;
    }
    .ft-stat-card {
        background: #171522; border: 1px solid #30283A;
        border-radius: 14px; padding: 18px 20px;
        box-shadow: 0 2px 10px rgba(44,30,26,0.04);
    }
    .ft-stat-value { font-size: 30px; font-weight: 800; color: #F5F3F7; }
    .ft-stat-label { font-size: 13px; color: #AAA3B5; margin-top: 2px; }

    .ft-divider { height: 1px; background: #30283A; margin: 28px 0; border: none; }

    /* Sidebar navigation */
    /* Extra specificity for Streamlit releases that apply a max-width after the initial CSS. */
    [data-testid="stSidebar"][aria-expanded="false"] ~ [data-testid="stMain"] *,
    [data-testid="stSidebar"][aria-expanded="false"] ~ [data-testid="stMain"] .block-container {
        box-sizing: border-box !important;
    }

    /* Keep the sidebar 255px only while it is open.  The collapsed sidebar
       must not reserve a 255px layout column. */
    [data-testid="stSidebar"][aria-expanded="true"] {
        min-width: 255px !important;
        max-width: 255px !important;
        width: 255px !important;
    }
    [data-testid="stSidebar"][aria-expanded="false"] {
        min-width: 0 !important;
        max-width: 0 !important;
        width: 0 !important;
        flex: 0 0 0 !important;
    }
    [data-testid="stSidebar"] .block-container { padding: 1.8rem 1.15rem 1.5rem 1.15rem !important; }
    .ft-side-brand { font-size: 20px; font-weight: 800; color: #F5F3F7 !important; margin-bottom: 2px; }
    .ft-side-sub { color: #AAA3B5 !important; font-size: 12.5px; line-height: 1.45; margin-bottom: 26px; }
    .ft-side-label { color: #9B4DFF !important; font-size: 11px; font-weight: 800; letter-spacing: 1.2px; text-transform: uppercase; margin: 0 0 8px 2px; }
    [data-testid="stSidebar"] div.stButton > button {
        width: 100% !important; min-height: 42px !important; margin: 0 0 7px 0 !important;
        padding: 8px 12px !important; text-align: left !important; justify-content: flex-start !important;
        border-radius: 9px !important; background: transparent !important; border: 1px solid transparent !important;
        color: #F5F3F7 !important; box-shadow: none !important; font-size: 14px !important;
    }
    [data-testid="stSidebar"] div.stButton > button:hover { background: rgba(155,77,255,0.14) !important; border-color: rgba(155,77,255,0.35) !important; color: #F5F3F7 !important; }
    [data-testid="stSidebar"] div.stButton > button[kind="primary"] { background: #9B4DFF !important; border-color: #C4B5FD !important; color: #0B0A0F !important; font-weight: 800 !important; box-shadow: 0 5px 18px rgba(155,77,255,0.22) !important; }
    [data-testid="stSidebar"] div.stButton > button[kind="primary"]:hover { background: #C4B5FD !important; color: #0B0A0F !important; }
    .ft-side-divider { height: 1px; background: rgba(48,40,58,0.9); margin: 18px 0; }
    .ft-side-current { background: #171522 !important; border: 1px solid #30283A !important; border-radius: 12px; padding: 13px; margin-top: 2px; }
    .ft-side-current-label { color: #542B72 !important; font-size: 11px; font-weight: 800; letter-spacing: .8px; margin-bottom: 7px; }
    .ft-side-current-value { color: #C4B5FD !important; font-weight: 800; font-size: 16px; margin-top: 10px; }

    /* ============================================================
       REPORTS — BLEND NATIVE DOWNLOAD / DATA CONTROLS INTO CANVAS
       ============================================================ */

    [data-testid="stDownloadButton"] {
        width: 100% !important;
    }

    [data-testid="stDownloadButton"] > button,
    [data-testid="stDownloadButton"] button {
        width: 100% !important;
        min-height: 48px !important;
        border-radius: 12px !important;
        background: rgba(23,21,34,0.94) !important;
        color: #F5F3F7 !important;
        border: 1px solid #30283A !important;
        box-shadow: 0 8px 24px rgba(0,0,0,0.18) !important;
        opacity: 1 !important;
    }

    [data-testid="stDownloadButton"] button:hover {
        background: #211A2B !important;
        border-color: #9B4DFF !important;
        color: #F5F3F7 !important;
    }

    [data-testid="stDownloadButton"] button p,
    [data-testid="stDownloadButton"] button span {
        color: #F5F3F7 !important;
        opacity: 1 !important;
    }

    /* Keep wide report tables inside the FraudTwin canvas. */
    [data-testid="stDataFrame"] {
        width: 100% !important;
        max-width: 100% !important;
        border: 1px solid #30283A !important;
        border-radius: 12px !important;
        overflow: hidden !important;
        background: rgba(23,21,34,0.78) !important;
    }

    /* The report page should never create a white native surface. */
    [data-testid="stDataFrame"] iframe,
    [data-testid="stDataFrame"] > div {
        background: transparent !important;
    }

    /* Native Streamlit controls */
    [data-baseweb="input"], [data-baseweb="select"], [data-baseweb="textarea"],
    [data-testid="stNumberInput"], [data-testid="stSelectbox"] {
        background: #171522 !important;
        color: #F5F3F7 !important;
    }
    [data-baseweb="input"] > div, [data-baseweb="select"] > div,
    [data-baseweb="textarea"] > div {
        background: #171522 !important;
        border-color: #30283A !important;
    }
    input, textarea {
        background: #171522 !important; color: #F5F3F7 !important;
        -webkit-text-fill-color: #F5F3F7 !important;
    }
    [data-baseweb="select"] *, [data-baseweb="input"] *, [data-baseweb="textarea"] * {
        color: #F5F3F7 !important;
    }
    [role="listbox"], [role="option"] {
        background: #171522 !important; color: #F5F3F7 !important;
    }
    [role="option"]:hover { background: #30283A !important; }

    div.stButton > button {
        border-radius: 10px !important; font-weight: 600 !important;
        border: 1px solid #30283A !important;
        background: #171522 !important; color: #F5F3F7 !important;
    }
    div.stButton > button:hover {
        border-color: #9B4DFF !important; color: #F5F3F7 !important;
        background: #211A2B !important;
    }
    div.stButton > button[kind="primary"] {
        background: #9B4DFF !important; color: #0B0A0F !important; border: none !important;
    }
    div.stButton > button[kind="primary"] p { color: #0B0A0F !important; }

    [data-testid="stAlert"] {
        background: #30283A !important; border-color: #9B4DFF !important;
        color: #F5F3F7 !important;
    }
    [data-testid="stExpander"] {
        background: #171522 !important; border: 1px solid #30283A !important;
    }
    [data-testid="stDataFrame"] {
        background: #171522 !important;
        border: 1px solid #30283A !important;
    }
    [data-testid="stProgressBar"] > div > div { background: #9B4DFF !important; }

    /* Sidebar navigation states */
    [data-testid="stSidebar"] div.stButton > button {
        background: transparent !important;
        color: #F5F3F7 !important;
        border-color: transparent !important;
        text-align: left !important;
    }
    [data-testid="stSidebar"] div.stButton > button:hover {
        background: rgba(155,77,255,0.12) !important;
        border-color: rgba(155,77,255,0.35) !important;
        color: #9B4DFF !important;
    }
    [data-testid="stSidebar"] div.stButton > button[kind="primary"] {
        background: #9B4DFF !important;
        color: #0B0A0F !important;
    }
    [data-testid="stSidebar"] div.stButton > button[kind="primary"] p {
        color: #0B0A0F !important;
    }

    /* Dark Bronze Intelligence finish */
    [data-testid="stAppViewContainer"] .main {
        background: radial-gradient(circle at 78% 0%, rgba(84,43,114,0.12), transparent 34%), #0B0A0F !important;
    }
    .ft-hero {
        background: linear-gradient(135deg, #171522 0%, #211A2B 62%, #111018 100%) !important;
        border-color: #30283A !important;
        box-shadow: 0 12px 35px rgba(0,0,0,0.28), inset 0 1px 0 rgba(196,181,253,0.08);
    }
    .ft-card, .ft-score-wrap, .ft-stat-card, .ft-indicator {
        background: #171522 !important;
        border-color: #30283A !important;
        box-shadow: 0 8px 24px rgba(0,0,0,0.20) !important;
    }
    .ft-card:hover {
        border-color: #542B72 !important;
        box-shadow: 0 10px 28px rgba(0,0,0,0.26), 0 0 0 1px rgba(201,154,74,0.08) !important;
    }
    .ft-hero-title, .ft-hero-sub { color: #F5F3F7 !important; }
    .ft-eyebrow { color: #C4B5FD !important; background: rgba(155,77,255,0.12) !important; }
    .ft-section-title, .ft-card-title, .ft-stat-value, .ft-score-number { color: #F5F3F7 !important; }
    .ft-section-sub, .ft-card-text, .ft-stat-label, .ft-score-label { color: #AAA3B5 !important; }
    [data-testid="stSidebar"], [data-testid="stSidebar"] > div:first-child {
        background: #111018 !important;
    }
    [data-testid="stSidebar"] { border-right: 1px solid #30283A !important; }
    [data-testid="stSidebar"] div.stButton > button[kind="primary"] {
        background: #9B4DFF !important;
        color: #0B0A0F !important;
        box-shadow: 0 5px 18px rgba(155,77,255,0.20) !important;
    }
    div.stButton > button[kind="primary"] {
        background: #9B4DFF !important; color: #0B0A0F !important; border: none !important;
        box-shadow: 0 5px 18px rgba(155,77,255,0.18) !important;
    }
    [data-testid="stProgressBar"] > div > div { background: #9B4DFF !important; }
    input, textarea, [data-baseweb="input"], [data-baseweb="select"], [data-baseweb="textarea"],
    [data-baseweb="input"] > div, [data-baseweb="select"] > div, [data-baseweb="textarea"] > div,
    [role="listbox"], [role="option"] {
        background: #111018 !important; color: #F5F3F7 !important;
    }
    input, textarea { -webkit-text-fill-color: #F5F3F7 !important; border-color: #30283A !important; }
    [role="option"]:hover { background: #211A2B !important; }
    [data-testid="stExpander"], [data-testid="stDataFrame"] {
        background: #171522 !important; border-color: #30283A !important;
    }
    [data-testid="stAlert"] {
        background: #211A2B !important; border-color: #542B72 !important; color: #F5F3F7 !important;
    }
    .ft-side-current {
        background: #171522 !important; border-color: #30283A !important;
    }
    .ft-side-current-value { color: #C4B5FD !important; }

    /* Final presentation polish: keep charts inside the dark FraudTwin canvas. */
    [data-testid="stVegaLiteChart"] {
        background: transparent !important;
        border: 1px solid #30283A !important;
        border-radius: 12px !important;
        padding: 8px !important;
        overflow: hidden !important;
    }
    .ft-ai-result, .ft-ai-result * { color: #F5F3F7 !important; }
    .ft-ai-result h1, .ft-ai-result h2, .ft-ai-result h3 { color: #F5F3F7 !important; }
    .ft-ai-result li, .ft-ai-result p { color: #E8E3EE !important; }
    @media (max-width: 900px) {
        .block-container { padding-left: 1rem !important; padding-right: 1rem !important; }
        .ft-score-wrap { padding: 20px !important; gap: 18px !important; }
        .ft-score-number { font-size: 46px !important; }
    }
    /* FINAL SIDEBAR-COLLAPSE ALIGNMENT
       The hidden sidebar must release its layout column.  The main workspace
       then becomes a centered canvas instead of staying offset to the right. */
    [data-testid="stSidebar"][aria-expanded="false"] ~ [data-testid="stMain"] {
        width: 100% !important;
        max-width: 100% !important;
        min-width: 0 !important;
        margin-left: 0 !important;
        margin-right: 0 !important;
        left: 0 !important;
        right: 0 !important;
        transform: none !important;
    }

    [data-testid="stSidebar"][aria-expanded="false"] ~ [data-testid="stMain"] > div,
    [data-testid="stSidebar"][aria-expanded="false"] ~ [data-testid="stMain"] [data-testid="stMainBlockContainer"],
    [data-testid="stSidebar"][aria-expanded="false"] ~ [data-testid="stMain"] .block-container {
        width: 100% !important;
        max-width: none !important;
        min-width: 0 !important;
        margin-left: 0 !important;
        margin-right: 0 !important;
        box-sizing: border-box !important;
        overflow-x: hidden !important;
    }

    /* Analyze form: never let Streamlit columns become wider than the visible canvas. */
    [data-testid="stMain"] [data-testid="stHorizontalBlock"] {
        width: 100% !important;
        max-width: 100% !important;
        min-width: 0 !important;
        box-sizing: border-box !important;
    }
    [data-testid="stMain"] [data-testid="stColumn"] {
        min-width: 0 !important;
        max-width: 100% !important;
        box-sizing: border-box !important;
    }
    [data-testid="stMain"] [data-testid="stColumn"] > div {
        max-width: 100% !important;
        min-width: 0 !important;
        box-sizing: border-box !important;
    }

    /* Prevent long selectbox labels and native controls from creating horizontal overflow. */
    [data-testid="stMain"] [data-baseweb="select"],
    [data-testid="stMain"] [data-baseweb="input"],
    [data-testid="stMain"] [data-testid="stNumberInput"],
    [data-testid="stMain"] [data-testid="stSelectbox"] {
        max-width: 100% !important;
        min-width: 0 !important;
        box-sizing: border-box !important;
    }

    @media (max-width: 900px) {
        [data-testid="stMain"] [data-testid="stHorizontalBlock"] {
            flex-wrap: wrap !important;
        }
        [data-testid="stMain"] [data-testid="stColumn"] {
            min-width: 100% !important;
            flex: 1 1 100% !important;
        }
    }

    [data-testid="stSidebar"][aria-expanded="false"] ~ [data-testid="stMain"] [data-testid="stHorizontalBlock"] {
        width: 100% !important;
        max-width: none !important;
    }

    @media (max-width: 900px) {
        [data-testid="stSidebar"][aria-expanded="false"] ~ [data-testid="stMain"] .block-container {
            max-width: 100% !important;
        }
    }

    </style>
    <div class="ft-background-art" aria-hidden="true">
        <svg viewBox="0 0 1100 720" preserveAspectRatio="none">
            <defs>
                <linearGradient id="ftLine" x1="0" x2="1">
                    <stop offset="0" stop-color="#542B72" stop-opacity="0"/>
                    <stop offset="0.42" stop-color="#9B4DFF" stop-opacity="0.78"/>
                    <stop offset="0.82" stop-color="#D946EF" stop-opacity="0.58"/>
                    <stop offset="1" stop-color="#C4B5FD" stop-opacity="0.10"/>
                </linearGradient>
            </defs>
            <rect x="80" y="70" width="910" height="590" rx="28" class="ft-art-panel"/>
            <g>
                <line x1="130" y1="150" x2="950" y2="150" class="ft-art-grid"/>
                <line x1="130" y1="250" x2="950" y2="250" class="ft-art-grid"/>
                <line x1="130" y1="350" x2="950" y2="350" class="ft-art-grid"/>
                <line x1="130" y1="450" x2="950" y2="450" class="ft-art-grid"/>
                <line x1="130" y1="550" x2="950" y2="550" class="ft-art-grid"/>
                <line x1="130" y1="120" x2="130" y2="585" class="ft-art-axis"/>
                <line x1="130" y1="585" x2="950" y2="585" class="ft-art-axis"/>
            </g>
            <path d="M130 500 L220 445 L285 470 L365 390 L440 420 L520 315 L600 355 L680 245 L760 285 L850 175 L950 215" class="ft-art-line"/>
            <path d="M130 525 L220 485 L285 505 L365 435 L440 460 L520 360 L600 395 L680 300 L760 325 L850 220 L950 255" class="ft-art-line-soft"/>
            <circle cx="680" cy="245" r="45" class="ft-art-ring"/>
            <circle cx="680" cy="245" r="68" class="ft-art-ring"/>
            <g opacity=".85">
                <rect x="165" y="555" width="26" height="30" class="ft-art-bar"/>
                <rect x="205" y="525" width="26" height="60" class="ft-art-bar"/>
                <rect x="245" y="545" width="26" height="40" class="ft-art-bar-bright"/>
                <rect x="285" y="495" width="26" height="90" class="ft-art-bar"/>
                <rect x="325" y="515" width="26" height="70" class="ft-art-bar-bright"/>
                <rect x="365" y="465" width="26" height="120" class="ft-art-bar"/>
                <rect x="405" y="485" width="26" height="100" class="ft-art-bar-bright"/>
            </g>
            <g opacity=".72">
                <rect x="760" y="105" width="150" height="95" rx="12" class="ft-art-panel"/>
                <circle cx="795" cy="140" r="18" class="ft-art-ring"/>
                <circle cx="795" cy="140" r="5" class="ft-art-node-pink"/>
                <line x1="825" y1="130" x2="880" y2="130" class="ft-art-grid"/>
                <line x1="825" y1="150" x2="895" y2="150" class="ft-art-grid"/>
                <line x1="825" y1="170" x2="865" y2="170" class="ft-art-grid"/>
            </g>
            <text x="145" y="105" class="ft-art-label">RISK INTELLIGENCE / LIVE SIGNALS</text>
            <text x="735" y="635" class="ft-art-label">FRAUDTWIN • AI ANALYTICS</text>
        </svg>
    </div>
    """, unsafe_allow_html=True)


def ft_line_chart(series, y_title):
    chart_df = pd.DataFrame({"Scenario": series.index.astype(str), "Risk Score": pd.to_numeric(series.values)})
    chart = (
        alt.Chart(chart_df)
        .mark_line(point=True, strokeWidth=2.5)
        .encode(
            x=alt.X("Scenario:N", title=None, axis=alt.Axis(labelColor="#AAA3B5", labelAngle=-45, grid=False)),
            y=alt.Y("Risk Score:Q", title=y_title, axis=alt.Axis(labelColor="#AAA3B5", titleColor="#AAA3B5", gridColor="#30283A")),
            tooltip=[alt.Tooltip("Scenario:N", title="Transaction"), alt.Tooltip("Risk Score:Q", format=".2f")]
        )
        .properties(background="transparent", height=330)
        .configure_view(strokeOpacity=0)
    )
    st.altair_chart(chart, use_container_width=True)


def ft_bar_chart(df, value_column, y_title):
    chart_df = df.reset_index()
    category_column = chart_df.columns[0]
    chart = (
        alt.Chart(chart_df)
        .mark_bar(cornerRadiusTopLeft=5, cornerRadiusTopRight=5)
        .encode(
            x=alt.X(f"{category_column}:N", title=None, axis=alt.Axis(labelColor="#AAA3B5", labelAngle=-35, grid=False)),
            y=alt.Y(f"{value_column}:Q", title=y_title, axis=alt.Axis(labelColor="#AAA3B5", titleColor="#AAA3B5", gridColor="#30283A")),
            tooltip=[alt.Tooltip(f"{category_column}:N", title="Category"), alt.Tooltip(f"{value_column}:Q", title="Score", format=".2f")]
        )
        .properties(background="transparent", height=330)
        .configure_view(strokeOpacity=0)
    )
    st.altair_chart(chart, use_container_width=True)


def risk_badge_html(level, icon=None):
    color = RISK_COLORS.get(level, "#AAA3B5")
    return (
        f'<span class="ft-badge" style="background:{color}22; color:{color}; '
        f'border-color:{color}55;">{level}</span>'
    )


def indicator_row(text, positive=False):
    icon = "PASS" if positive else "FLAG"
    st.markdown(f'<div class="ft-indicator"><span class="ft-status-marker">{icon}</span><span>{text}</span></div>', unsafe_allow_html=True)


def stat_card(value, label):
    st.markdown(
        f'<div class="ft-stat-card"><div class="ft-stat-value">{value}</div>'
        f'<div class="ft-stat-label">{label}</div></div>',
        unsafe_allow_html=True
    )


def section_title(title, subtitle=None):
    st.markdown(f'<div class="ft-section-title">{title}</div>', unsafe_allow_html=True)
    if subtitle:
        st.markdown(f'<div class="ft-section-sub">{subtitle}</div>', unsafe_allow_html=True)


def score_hero(score, level, icon, decision):
    color = RISK_COLORS.get(level, "#AAA3B5")
    st.markdown(
        f"""
        <div class="ft-score-wrap">
            <div>
                <div class="ft-score-label">Risk Intelligence Score</div>
                <div class="ft-score-number" style="color:{color};">{score:.0f}<span style="font-size:22px;color:#AAA3B5;">/100</span></div>
            </div>
            <div style="flex:1; min-width:220px;">
                {risk_badge_html(level, icon)}
                <div style="margin-top:10px; color:#AAA3B5; font-size:14px;">
                    Recommended action: <strong style="color:#F5F3F7;">{decision}</strong>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.progress(min(max(int(score), 0), 100))


# ============================================================
# LIVE RISK MONITOR
# ============================================================

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
# PAGE: RISK DASHBOARD
# ============================================================

def page_risk_dashboard():
    # Legacy helper retained for compatibility; dashboard is now embedded in Reports.
    section_title("Risk Dashboard", "Dashboard view embedded in Reports")

    history = st.session_state.risk_history

    if not history:
        st.info("No transactions analyzed yet. Head to **Analyze** to score your first transaction.")
        return

    df = pd.DataFrame(history)
    total = len(df)
    high = int((df["Risk Level"] == "HIGH RISK").sum())
    medium = int((df["Risk Level"] == "MEDIUM RISK").sum())
    low = int((df["Risk Level"] == "LOW RISK").sum())
    avg_score = df["Risk Score"].astype(float).mean()

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1: stat_card(total, "Transactions Analyzed")
    with c2: stat_card(f"{avg_score:.0f}/100", "Average Risk Score")
    with c3: stat_card(high, "High Risk")
    with c4: stat_card(medium, "Medium Risk")
    with c5: stat_card(low, "Low Risk")

    st.markdown("<div class='ft-divider'></div>", unsafe_allow_html=True)

    left, right = st.columns([1.3, 1])
    with left:
        section_title("Risk score over time")
        chart_df = df.copy()
        chart_df.index = [f"Txn {i+1}" for i in range(len(chart_df))]
        ft_line_chart(chart_df["Risk Score"], "Risk Intelligence Score")

    with right:
        section_title("Risk distribution")
        dist_df = pd.DataFrame({
            "Level": ["High", "Medium", "Low"],
            "Count": [high, medium, low]
        }).set_index("Level")
        ft_bar_chart(dist_df, "Count", "Count")

    st.markdown("<div class='ft-divider'></div>", unsafe_allow_html=True)
    section_title("Important alerts", "Most recent high and medium risk transactions")

    alerts = df[df["Risk Level"].isin(["HIGH RISK", "MEDIUM RISK"])].tail(5).iloc[::-1]
    if alerts.empty:
        indicator_row("No high or medium risk transactions recorded yet.", positive=True)
    else:
        for _, row in alerts.iterrows():
            icon = "HIGH" if row["Risk Level"] == "HIGH RISK" else "MEDIUM"
            indicator_row(
                f"₹{float(row['Amount']):,.2f} at {row['Transaction Time']} — "
                f"{row['Risk Level']} ({float(row['Risk Score']):.0f}/100) — {row['Decision']}"
            )

    with st.expander("View full transaction table"):
        st.dataframe(df, width="stretch", hide_index=True)


# ============================================================
# PAGE: TRANSACTION ANALYSIS
# ============================================================

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


# ============================================================
# PAGE: AI RISK MANAGER
# ============================================================

def page_ai_risk_manager():
    section_title(" AI Risk Manager", "AI-generated, plain-language decision support — it never changes the ML score")

    if not st.session_state.analyzed or st.session_state.analysis_data is None:
        st.info("Analyze a transaction first on the **Analyze** page, then come back here.")
        return

    data = st.session_state.analysis_data
    attack_result = st.session_state.attack_result

    attack_score = attack_result.get("stress_score") if attack_result else None
    attack_indicators = attack_result.get("attack_indicators", 0) if attack_result else 0

    c1, c2, c3 = st.columns(3)
    with c1: stat_card(f"{data['final_score']:.0f}/100", "Current Risk Score")
    with c2: stat_card(data["decision"], "Current Decision")
    with c3: stat_card(f"{attack_score:.0f}/100" if attack_score is not None else "—", "Attack Stress Score")

    st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
    st.info("This is decision support for a human risk manager — it does not replace or modify the FraudTwin Risk Intelligence Score.")

    if st.button(" Generate AI Risk Assessment", type="primary", width="stretch", key="generate_ai_assessment"):
        try:
            with st.spinner("AI Risk Manager is analyzing the transaction..."):
                st.session_state.ai_result = generate_ai_risk_assessment(
                    amount=data["amount"], transaction_hour=data["hour"], device=data["device"],
                    location=data["location"], transaction_type=data["type"],
                    ml_probability=data["probability"], context_score=data["context_score"],
                    final_risk_score=data["final_score"], risk_level=data["level"], decision=data["decision"],
                    contextual_factors=data["factors"], attack_score=attack_score, attack_indicators=attack_indicators
                )
        except Exception as e:
            st.session_state.ai_result = None
            st.error("The AI Risk Manager could not generate an assessment.")
            st.caption(f"Technical detail: {str(e)}")

    if st.session_state.ai_result:
        st.markdown("<div class='ft-divider'></div>", unsafe_allow_html=True)
        st.success("AI Risk Assessment generated successfully.")
        st.markdown(st.session_state.ai_result)


# ============================================================
# PAGE: INVESTIGATION CENTER
# ============================================================

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


# ============================================================
# PAGE: REPORTS & INSIGHTS
# ============================================================

def page_reports():
    section_title("Reports", "Risk dashboard, transaction history, trends, and investigation cases")

    history = st.session_state.risk_history

    # Reports is the single destination for analytics and audit history.
    if history:
        df = pd.DataFrame(history)
        total = len(df)
        high = int((df["Risk Level"] == "HIGH RISK").sum())
        medium = int((df["Risk Level"] == "MEDIUM RISK").sum())
        low = int((df["Risk Level"] == "LOW RISK").sum())
        avg_score = df["Risk Score"].astype(float).mean()

        c1, c2, c3, c4 = st.columns(4)
        with c1: stat_card(total, "Transactions Analyzed")
        with c2: stat_card(f"{avg_score:.0f}/100", "Average Risk Score")
        with c3: stat_card(high, "High Risk")
        with c4: stat_card(medium + low, " Medium / Low")

        st.markdown("<div class='ft-divider'></div>", unsafe_allow_html=True)

        left, right = st.columns([1.3, 1])
        with left:
            section_title("Risk score over time")
            chart_df = df.copy()
            chart_df.index = [f"Txn {i+1}" for i in range(len(chart_df))]
            ft_line_chart(chart_df["Risk Score"], "Risk Intelligence Score")
        with right:
            section_title("Risk distribution")
            dist_df = pd.DataFrame({
                "Level": ["High", "Medium", "Low"],
                "Count": [high, medium, low]
            }).set_index("Level")
            ft_bar_chart(dist_df, "Count", "Count")

        st.markdown("<div class='ft-divider'></div>", unsafe_allow_html=True)

    tab1, tab2 = st.tabs([" Transaction History", " Investigation Cases"])

    with tab1:
        if not history:
            st.info("No transaction history yet. Analyze a transaction to create the first record.")
        else:
            df = pd.DataFrame(history)
            c1, c2, c3 = st.columns(3)
            with c1: stat_card(len(df), "Transactions Analyzed")
            with c2: stat_card(int((df["Risk Level"] == "HIGH RISK").sum()), "High Risk")
            with c3: stat_card(int((df["Risk Level"] == "MEDIUM RISK").sum()), "Medium Risk")

            display_history = df.copy()
            display_history["Amount"] = display_history["Amount"].apply(lambda x: f"₹{x:,.2f}")
            display_history["ML Probability"] = display_history["ML Probability"].apply(lambda x: f"{x:.2f}%")
            display_history["Context Risk"] = display_history["Context Risk"].apply(lambda x: f"{x:.0f}/30")
            display_history["Risk Score"] = display_history["Risk Score"].apply(lambda x: f"{x:.2f}/100")
            st.dataframe(display_history, width="stretch", hide_index=True)

            highest_risk = max(history, key=lambda x: x["Risk Score"])
            section_title(" Highest Risk Transaction")
            c1, c2 = st.columns(2)
            with c1:
                st.metric("Highest Risk Score", f"{highest_risk['Risk Score']:.2f}/100")
                st.write(f"**Amount:** ₹{highest_risk['Amount']:,.2f}")
                st.write(f"**Time:** {highest_risk['Transaction Time']}")
            with c2:
                st.write(f"**Device:** {highest_risk['Device']}")
                st.write(f"**Location:** {highest_risk['Location']}")
                st.write(f"**Decision:** {highest_risk['Decision']}")

            export_csv = pd.DataFrame(history).to_csv(index=False).encode("utf-8")
            e1, e2 = st.columns(2)
            with e1:
                st.download_button(" Export Transaction History (CSV)", data=export_csv,
                                    file_name="fraudtwin_transaction_history.csv", mime="text/csv", width="stretch")
            with e2:
                if st.button(" Clear Transaction History", width="stretch"):
                    st.session_state.risk_history = []
                    save_risk_history()
                    st.rerun()

    with tab2:
        if not st.session_state.investigation_history:
            st.info("No investigation cases have been saved yet.")
        else:
            inv_df = pd.DataFrame(st.session_state.investigation_history).iloc[::-1].reset_index(drop=True)
            cols = ["Case ID", "Created", "Amount", "Risk Score", "Alert Priority", "Status", "Decision", "Notes"]
            available = [c for c in cols if c in inv_df.columns]
            display_inv = inv_df[available].copy()
            if "Amount" in display_inv.columns:
                display_inv["Amount"] = display_inv["Amount"].apply(lambda v: f"₹{float(v):,.2f}")
            if "Risk Score" in display_inv.columns:
                display_inv["Risk Score"] = display_inv["Risk Score"].apply(lambda v: f"{float(v):.2f}/100")
            st.dataframe(display_inv, width="stretch", hide_index=True)
            st.caption(f" {len(st.session_state.investigation_history)} investigation case(s) saved.")


# ============================================================
# MAIN — NAVIGATION SHELL
# ============================================================

def main():
    inject_css()

    with st.sidebar:
        st.markdown("<div class='ft-side-brand'> FraudTwin</div>", unsafe_allow_html=True)
        st.markdown("<div class='ft-side-sub'>AI-Powered Transaction Risk Intelligence</div>", unsafe_allow_html=True)
        st.markdown("<div class='ft-side-label'>Navigation</div>", unsafe_allow_html=True)

        current_page = st.session_state.page
        for index, nav_item in enumerate(NAV_PAGES):
            if st.button(
                nav_item,
                key=f"sidebar_nav_{index}",
                type="primary" if nav_item == current_page else "secondary",
                width="stretch",
            ):
                if st.session_state.page != nav_item:
                    st.session_state.page = nav_item
                    st.rerun()

        st.markdown("<div class='ft-side-divider'></div>", unsafe_allow_html=True)

        if st.session_state.analyzed and st.session_state.analysis_data:
            d = st.session_state.analysis_data
            st.markdown("<div class='ft-side-current'>", unsafe_allow_html=True)
            st.markdown("<div class='ft-side-current-label'>CURRENT TRANSACTION</div>", unsafe_allow_html=True)
            st.markdown(risk_badge_html(d["level"], d["icon"]), unsafe_allow_html=True)
            st.markdown(f"<div class='ft-side-current-value'>₹{d['amount']:,.2f}</div>", unsafe_allow_html=True)
            st.markdown(f"<div style='color:#AAA3B5 !important;font-size:11.5px;margin-top:5px;'>Transaction time · {d['hour']:02d}:00</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
            st.markdown("<div class='ft-side-divider'></div>", unsafe_allow_html=True)

        st.markdown("<div style='color:#AAA3B5;font-size:11.5px;line-height:1.6;'>Analyze transactions · Investigate alerts · Review reports</div>", unsafe_allow_html=True)

    page = st.session_state.page
    if page == "Home":
        page_home()
    elif page == "Analyze":
        page_transaction_analysis()
    elif page == "Investigate":
        page_investigation_center()
    elif page == "Reports":
        page_reports()


if __name__ == "__main__":
    main()