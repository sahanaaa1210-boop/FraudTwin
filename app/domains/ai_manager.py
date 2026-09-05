import time

import streamlit as st
from google import genai


# ============================================================
# FRAUDTWIN — AI MANAGER
# ============================================================


def generate_ai_risk_assessment(
    amount,
    transaction_hour,
    device,
    location,
    transaction_type,
    ml_probability,
    context_score,
    final_risk_score,
    risk_level,
    decision,
    contextual_factors,
    attack_score=None,
    attack_indicators=0
):
    """
    Use Gemini as decision-support for the existing FraudTwin risk engine.
    The ML Risk Intelligence Score is never changed by the AI.
    """

    api_key = st.secrets.get("GEMINI_API_KEY")

    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY was not found in .streamlit/secrets.toml."
        )

    client = genai.Client(api_key=api_key)

    factors_text = (
        "\n".join(
            f"- {factor}"
            for factor in contextual_factors
        )
        if contextual_factors
        else "- No contextual risk factors detected"
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

    configured_model = st.secrets.get(
        "GEMINI_MODEL",
        "gemini-3.7-flash"
    )

    model_candidates = []

    for candidate in [
        configured_model,
        "gemini-3.7-flash",
        "gemini-3.6-flash",
        "gemini-3.5-flash-lite"
    ]:
        if candidate and candidate not in model_candidates:
            model_candidates.append(candidate)

    last_error = None

    for model_name in model_candidates:

        for attempt in range(2):

            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt
                )

                if (
                    response is None
                    or not getattr(response, "text", None)
                ):
                    raise ValueError(
                        f"Gemini returned an empty response from {model_name}."
                    )

                return response.text.strip()

            except Exception as error:

                last_error = error
                error_text = str(error).lower()

                temporary_error = any(
                    marker in error_text
                    for marker in [
                        "503",
                        "unavailable",
                        "high demand",
                        "temporarily",
                        "deadline exceeded",
                        "internal server error"
                    ]
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