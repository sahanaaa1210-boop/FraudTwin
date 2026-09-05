from pathlib import Path


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent.parent

MODEL_PATH = BASE_DIR / "models" / "fraud_model.pkl"
SCALER_PATH = BASE_DIR / "models" / "scaler.pkl"

DATA_DIR = BASE_DIR / "data"

HISTORY_FILE = DATA_DIR / "transaction_history.csv"
INVESTIGATION_FILE = DATA_DIR / "investigation_cases.json"


# ============================================================
# FEATURE CONSTANTS
# ============================================================

FEATURE_NAMES = [
    "Time",
    *[f"V{i}" for i in range(1, 29)],
    "Amount",
]


# ============================================================
# TRANSACTION OPTIONS
# ============================================================

DEVICE_OPTIONS = [
    "Trusted Device",
    "New Device",
]

LOCATION_OPTIONS = [
    "Usual Location",
    "Unusual Location",
]

TYPE_OPTIONS = [
    "Normal Purchase",
    "Online Purchase",
    "Large Transfer",
]


# ============================================================
# RISK WEIGHTS
# ============================================================

ML_WEIGHT = 0.80
CONTEXT_WEIGHT = 0.20
MAX_CONTEXT_POINTS = 30


# ============================================================
# NAVIGATION
# ============================================================

NAV_PAGES = [
    "Home",
    "Analyze",
    "Investigate",
    "Reports",
]


# ============================================================
# RISK COLORS
# ============================================================

RISK_COLORS = {
    "HIGH RISK": "#E05260",
    "MEDIUM RISK": "#D6A84F",
    "LOW RISK": "#45A56A",
    "SEVERE ATTACK": "#E05260",
    "HIGH ATTACK RISK": "#E05260",
    "MODERATE ATTACK RISK": "#D6A84F",
    "LOW ATTACK IMPACT": "#45A56A",
}