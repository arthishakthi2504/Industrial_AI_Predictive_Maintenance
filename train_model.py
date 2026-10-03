import os
import pandas as pd
import joblib

from sklearn.ensemble import IsolationForest


# ==========================================
# FILE PATHS
# ==========================================

DATA_FILE = "data/machine_data.csv"
MODEL_FILE = "ml/anomaly_model.pkl"


# ==========================================
# CREATE ML FOLDER
# ==========================================

os.makedirs("ml", exist_ok=True)


# ==========================================
# START
# ==========================================

print("======================================")
print("       INDUSTRIAL AI MODEL")
print("======================================")


# ==========================================
# LOAD DATASET
# ==========================================

data = pd.read_csv(DATA_FILE)

print()
print("Dataset loaded successfully.")
print("Total records:", len(data))


# ==========================================
# SELECT NORMAL DATA
# ==========================================

normal_data = data[
    data["status"] == "NORMAL"
]

print(
    "Normal records used for training:",
    len(normal_data)
)


# ==========================================
# SENSOR FEATURES
# ==========================================

features = [
    "temperature",
    "vibration",
    "current",
    "rpm"
]


X = normal_data[features]


# ==========================================
# CREATE ISOLATION FOREST
# ==========================================

model = IsolationForest(
    n_estimators=150,
    contamination=0.05,
    random_state=42
)


# ==========================================
# TRAIN MODEL
# ==========================================

print()
print("Training AI model...")

model.fit(X)


# ==========================================
# SAVE MODEL
# ==========================================

joblib.dump(
    model,
    MODEL_FILE
)


print()
print("AI model training completed successfully.")

print(
    "Model saved at:",
    MODEL_FILE
)


# ==========================================
# TEST MODEL
# ==========================================

print()
print("Testing trained model...")

predictions = model.predict(X)

normal_count = sum(
    predictions == 1
)

anomaly_count = sum(
    predictions == -1
)


print(
    "Normal predictions:",
    normal_count
)

print(
    "Anomaly predictions:",
    anomaly_count
)


print()
print("======================================")
print("       AI TRAINING COMPLETE")
print("======================================")