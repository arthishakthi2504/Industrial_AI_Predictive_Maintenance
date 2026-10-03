import pandas as pd
import joblib


# ==========================================
# LOAD TRAINED AI MODEL
# ==========================================

MODEL_FILE = "ml/anomaly_model.pkl"

model = joblib.load(MODEL_FILE)

print("======================================")
print("       AI MODEL TEST")
print("======================================")

print()
print("Trained model loaded successfully.")


# ==========================================
# TEST CONDITIONS
# ==========================================

test_data = pd.DataFrame([
    {
        "temperature": 45.0,
        "vibration": 0.40,
        "current": 2.5,
        "rpm": 1420
    },

    {
        "temperature": 60.0,
        "vibration": 0.65,
        "current": 3.8,
        "rpm": 1300
    },

    {
        "temperature": 85.0,
        "vibration": 1.00,
        "current": 6.0,
        "rpm": 1100
    }
])


# ==========================================
# AI PREDICTION
# ==========================================

predictions = model.predict(test_data)


# ==========================================
# DISPLAY RESULTS
# ==========================================

print()
print("--------------------------------------")
print("AI TEST RESULTS")
print("--------------------------------------")


for i, prediction in enumerate(predictions):

    temperature = test_data.iloc[i]["temperature"]
    vibration = test_data.iloc[i]["vibration"]
    current = test_data.iloc[i]["current"]
    rpm = test_data.iloc[i]["rpm"]

    if prediction == 1:
        status = "NORMAL"
    else:
        status = "ANOMALY"

    print()
    print(f"Test {i + 1}")
    print(f"Temperature : {temperature} °C")
    print(f"Vibration   : {vibration}")
    print(f"Current     : {current} A")
    print(f"RPM         : {rpm}")
    print(f"AI Result   : {status}")


print()
print("======================================")
print("          TEST COMPLETED")
print("======================================")