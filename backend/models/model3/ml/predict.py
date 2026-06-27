import numpy as np
import joblib
import os

# -------------------------------
# PATH SETUP (FIXED ✅)
# -------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MODEL_PATH = os.path.join(BASE_DIR, "rf_model.pkl")
SCALER_PATH = os.path.join(BASE_DIR, "rf_scaler.pkl")

MODEL_PATH = os.path.abspath(MODEL_PATH)
SCALER_PATH = os.path.abspath(SCALER_PATH)

# -------------------------------
# CHECK MODEL EXISTS
# -------------------------------
def model_exists():
    return os.path.exists(MODEL_PATH) and os.path.exists(SCALER_PATH)

# -------------------------------
# LOAD MODEL
# -------------------------------
rf = None
scaler = None

def load_model():
    global rf, scaler

    print("📦 Model 3 paths:")
    print("MODEL:", MODEL_PATH)
    print("SCALER:", SCALER_PATH)

    if not model_exists():
        raise FileNotFoundError(
            f"\n❌ Model 3 files NOT found:\n{MODEL_PATH}\n{SCALER_PATH}"
        )

    rf = joblib.load(MODEL_PATH)
    scaler = joblib.load(SCALER_PATH)

    print("✅ Model 3 loaded successfully")

# Load at startup
load_model()

# -------------------------------
# PREDICT CURVES (FIXED ✅)
# -------------------------------
def predict_curves(T, RH, time, isos, PCE0, Voc0, Jsc0, FF0):

    if rf is None or scaler is None:
        raise RuntimeError("❌ Model not loaded properly.")

    print("🔍 Inputs:", T, RH, time, isos, PCE0, Voc0, Jsc0, FF0)

    isos_map = {
        "ISOS-D-1": 0,
        "ISOS-D-2": 1,
        "ISOS-L-1": 2,
        "ISOS-L-2": 3,
        "ISOS-O-1": 4
    }

    isos_val = isos_map.get(isos, 0)

    # ✅ FIX 1: MORE POINTS (smooth graph like Streamlit)
    times = np.linspace(0, time, 300)

    # ✅ FIX 2: VECTORIZED (same as training code)
    X = np.column_stack([
        np.full(300, T),
        np.full(300, RH),
        times,
        np.full(300, isos_val),
        np.full(300, PCE0),
        np.full(300, Voc0),
        np.full(300, Jsc0),
        np.full(300, FF0),
    ]).astype(np.float32)

    try:
        X_scaled = scaler.transform(X)
        preds = rf.predict(X_scaled)
    except Exception as e:
        raise RuntimeError(f"❌ Prediction error: {e}")

    # ✅ FIX 3: CLIP (same as original model)
    preds = np.clip(preds, 0.001, None)

    return (
        times,
        preds[:, 0],  # PCE
        preds[:, 1],  # Voc
        preds[:, 2],  # Jsc
        preds[:, 3],  # FF
    )

# -------------------------------
# METRICS FUNCTION (MATCH STREAMLIT ✅)
# -------------------------------
def compute_metrics(pce_start, times, pce):

    if len(pce) == 0:
        raise ValueError("❌ Empty prediction array")

    pce_final = float(pce[-1])
    total_time = float(times[-1])

    # ✅ EXACT SAME FORMULA
    eff_loss = round(((pce_start - pce_final) / pce_start) * 100.0, 3)

    deg_rate = round(
        (pce_start - pce_final) / total_time, 6
    ) if total_time > 0 else 0.0

    def find_time(frac):
        idx = np.where(pce <= pce_start * frac)[0]
        return float(times[idx[0]]) if len(idx) > 0 else None

    T90 = find_time(0.90)
    T80 = find_time(0.80)
    T50 = find_time(0.50)

    RUL = round(T80, 1) if T80 is not None else None

    return eff_loss, deg_rate, T90, T80, T50, RUL