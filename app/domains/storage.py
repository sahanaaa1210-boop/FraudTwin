import json
from datetime import datetime

import pandas as pd
import streamlit as st

from domains.config import (
    DATA_DIR,
    HISTORY_FILE,
    INVESTIGATION_FILE,
)


# ============================================================
# FRAUDTWIN — STORAGE
# ============================================================


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
            file,
            indent=2,
            ensure_ascii=False,
            default=str,
        )


def save_risk_history():
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    if st.session_state.risk_history:
        pd.DataFrame(
            st.session_state.risk_history
        ).to_csv(
            HISTORY_FILE,
            index=False
        )
    else:
        pd.DataFrame().to_csv(
            HISTORY_FILE,
            index=False
        )


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

    for index, case in enumerate(
        st.session_state.investigation_history
    ):
        if case.get("Case ID") == case_id:
            st.session_state.investigation_history[index] = dict(
                st.session_state.investigation_case
            )
            save_investigation_history()
            return