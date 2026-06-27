import numpy as np
import tensorflow as tf
import pickle
import json
import os

# -------------------------------
# LOAD FILES SAFELY ✅
# -------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

MODEL_PATH = os.path.join(BASE_DIR, "..", "models", "model1", "perovskite_mlp_model.keras")
SCALER_PATH = os.path.join(BASE_DIR, "..", "models", "model1", "scaler.pkl")
TARGET_SCALER_PATH = os.path.join(BASE_DIR, "..", "models", "model1", "target_scaler.pkl")
FEATURE_PATH = os.path.join(BASE_DIR, "..", "models", "model1", "feature_names.json")

MODEL_PATH = os.path.abspath(MODEL_PATH)
SCALER_PATH = os.path.abspath(SCALER_PATH)
TARGET_SCALER_PATH = os.path.abspath(TARGET_SCALER_PATH)
FEATURE_PATH = os.path.abspath(FEATURE_PATH)

print("📦 Model1 paths:")
print("MODEL:", MODEL_PATH)
print("SCALER:", SCALER_PATH)
print("TARGET:", TARGET_SCALER_PATH)
print("FEATURES:", FEATURE_PATH)

# -------------------------------
# LOAD MODELS
# -------------------------------
try:
    model = tf.keras.models.load_model(MODEL_PATH)
    feature_scaler = pickle.load(open(SCALER_PATH, "rb"))
    target_scaler = pickle.load(open(TARGET_SCALER_PATH, "rb"))
    feature_names = json.load(open(FEATURE_PATH))

    print("✅ Model 1 loaded successfully")

except Exception as e:
    print("❌ Model1 loading error:", e)
    model = None

# -------------------------------
# PREDICT FUNCTION
# -------------------------------
def predict_tabular(data):

    try:
        if model is None:
            raise RuntimeError("Model1 not loaded")

        print("📥 Incoming data:", data)

        # ✅ SAFE FEATURE EXTRACTION
        X = []
        for f in feature_names:
            value = data.get(f, 0)  # ← avoids crash
            X.append(float(value))

        X = np.array(X).reshape(1, -1)

        # ✅ SCALE
        X_scaled = feature_scaler.transform(X)

        # ✅ PREDICT
        pred_scaled = model.predict(X_scaled, verbose=0)
        pred = target_scaler.inverse_transform(pred_scaled)[0]

        result = {
            "pce": float(pred[0]),
            "voc": float(pred[1]),
            "jsc": float(pred[2]),
            "ff": float(pred[3])
        }

        print("✅ Model1 Output:", result)

        return result

    except Exception as e:
        print("❌ Model1 Prediction Error:", str(e))

        # 🔥 VERY IMPORTANT: RETURN SAFE RESPONSE
        return {
            "pce": 0.0,
            "voc": 0.0,
            "jsc": 0.0,
            "ff": 0.0,
            "error": str(e)
        }