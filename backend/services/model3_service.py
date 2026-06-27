from models.model3.ml.predict import predict_curves, compute_metrics

def predict_degradation(pce, voc, jsc, ff, T, RH, time, isos):

    # 👉 IMPORTANT: treat incoming PCE as STARTING PCE
    pce_start = float(pce)

    times, pce_arr, voc_arr, jsc_arr, ff_arr = predict_curves(
        T, RH, time, isos,
        pce_start,   # ✅ correct
        float(voc),
        float(jsc),
        float(ff)
    )

    efficiency_loss, deg_rate, T90, T80, T50, RUL = compute_metrics(
        pce_start, times, pce_arr
    )

    return {
        "curves": {
            "time": times.tolist(),
            "pce": pce_arr.tolist(),

            # 🔥 NORMALIZED VALUES (MATCH STREAMLIT)
            "voc": (voc_arr / voc_arr[0]).tolist(),
            "jsc": (jsc_arr / jsc_arr[0]).tolist(),
            "ff": (ff_arr / ff_arr[0]).tolist(),
        },
        "final_pce": float(pce_arr[-1]),
        "efficiency_loss": float(efficiency_loss),
        "deg_rate": float(deg_rate),
        "T90": T90,
        "T80": T80,
        "T50": T50,
        "RUL": RUL
    }