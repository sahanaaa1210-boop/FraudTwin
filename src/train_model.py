import pandas as pd
import numpy as np
import joblib

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score

from imblearn.over_sampling import SMOTE
from xgboost import XGBClassifier


# ==========================================
# 1. LOAD DATASET
# ==========================================

print("Loading dataset...")

df = pd.read_csv("data/creditcard.csv")

print("Dataset loaded!")
print("Shape:", df.shape)


# ==========================================
# 2. SEPARATE FEATURES AND TARGET
# ==========================================

X = df.drop("Class", axis=1)
y = df["Class"]

print("\nFraud distribution:")
print(y.value_counts())


# ==========================================
# 3. TRAIN / TEST SPLIT
# ==========================================

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42,
    stratify=y
)

print("\nTraining samples:", len(X_train))
print("Testing samples:", len(X_test))


# ==========================================
# 4. SCALE AMOUNT AND TIME
# ==========================================

scaler = StandardScaler()

X_train = X_train.copy()
X_test = X_test.copy()

X_train[["Time", "Amount"]] = scaler.fit_transform(
    X_train[["Time", "Amount"]]
)

X_test[["Time", "Amount"]] = scaler.transform(
    X_test[["Time", "Amount"]]
)


# ==========================================
# 5. HANDLE CLASS IMBALANCE
# ==========================================

print("\nApplying SMOTE...")

smote = SMOTE(random_state=42)

X_train_resampled, y_train_resampled = smote.fit_resample(
    X_train,
    y_train
)

print("Original training data:", len(X_train))
print("After SMOTE:", len(X_train_resampled))


# ==========================================
# 6. TRAIN XGBOOST MODEL
# ==========================================

print("\nTraining FraudTwin AI model...")

model = XGBClassifier(
    n_estimators=200,
    max_depth=6,
    learning_rate=0.1,
    subsample=0.8,
    colsample_bytree=0.8,
    objective="binary:logistic",
    eval_metric="logloss",
    random_state=42,
    n_jobs=-1
)

model.fit(
    X_train_resampled,
    y_train_resampled
)

print("Model training completed!")


# ==========================================
# 7. PREDICTIONS
# ==========================================

y_pred = model.predict(X_test)
y_probability = model.predict_proba(X_test)[:, 1]


# ==========================================
# 8. MODEL EVALUATION
# ==========================================

print("\n==============================")
print("MODEL PERFORMANCE")
print("==============================")

print("\nClassification Report:")
print(classification_report(y_test, y_pred))

print("\nConfusion Matrix:")
print(confusion_matrix(y_test, y_pred))

auc = roc_auc_score(y_test, y_probability)

print("\nROC-AUC Score:", round(auc, 4))


# ==========================================
# 9. SAVE MODEL AND SCALER
# ==========================================

joblib.dump(model, "models/fraud_model.pkl")
joblib.dump(scaler, "models/scaler.pkl")

print("\n==============================")
print("MODEL SAVED SUCCESSFULLY!")
print("==============================")
print("models/fraud_model.pkl")
print("models/scaler.pkl")