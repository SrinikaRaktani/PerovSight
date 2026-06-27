from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import json

# Services
from services.model1_service import predict_tabular
from services.model2_service import predict_image
from services.model3_service import predict_degradation

app = FastAPI(title="Multi-Modal Solar AI")

# -------------------------------
# CORS (IMPORTANT)
# -------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------
# TABULAR MODEL
# -------------------------------
@app.post("/predict/tabular")
async def tabular_prediction(data: dict):
    try:
        result = predict_tabular(data)
        return result
    except Exception as e:
        return {"error": str(e)}

# -------------------------------
# IMAGE MODEL
# -------------------------------
@app.post("/predict/image")
async def image_prediction(file: UploadFile = File(...)):
    try:
        result = await predict_image(file)
        return result
    except Exception as e:
        return {"error": str(e)}

# -------------------------------
# DEGRADATION MODEL
# -------------------------------
@app.post("/predict/degradation")
async def degradation_prediction(
    pce: float = Form(...),
    voc: float = Form(...),
    jsc: float = Form(...),
    ff: float = Form(...),
    temperature: float = Form(...),
    humidity: float = Form(...),
    time: int = Form(...),
    isos: str = Form(...)
):
    try:
        result = predict_degradation(
            float(pce), float(voc), float(jsc), float(ff),
            float(temperature), float(humidity), int(time), isos
        )
        return result

    except Exception as e:
        return {"error": str(e)}

# -------------------------------
# FULL PIPELINE (IMPORTANT 🔥)
# -------------------------------
@app.post("/predict/full")
async def full_pipeline(
    file: UploadFile = File(None),
    data: str = Form(None),
    run_degradation: bool = Form(False),
    temperature: float = Form(30),
    humidity: float = Form(50),
    time: int = Form(1000),
    isos: str = Form("ISOS-D-1")
):

    try:
        # -------------------------------
        # STEP 1: MODEL 1 or MODEL 2
        # -------------------------------
        if file:
            model_out = await predict_image(file)
            model_used = "image"

        else:
            data_dict = json.loads(data)
            model_out = predict_tabular(data_dict)
            model_used = "tabular"

        # Safety check
        if "error" in model_out:
            return {"status": "error", "message": model_out["error"]}

        pce = float(model_out["pce"])
        voc = float(model_out["voc"])
        jsc = float(model_out["jsc"])
        ff  = float(model_out["ff"])

        # -------------------------------
        # STEP 2: MODEL 3 (OPTIONAL)
        # -------------------------------
        degradation = None

        if run_degradation:
            degradation = predict_degradation(
                pce, voc, jsc, ff,
                float(temperature), float(humidity), int(time), isos
            )

            if isinstance(degradation, dict) and "error" in degradation:
                return {"status": "error", "message": degradation["error"]}

        # -------------------------------
        # FINAL RESPONSE
        # -------------------------------
        return {
            "status": "success",
            "model_used": model_used,
            "initial_results": model_out,
            "degradation": degradation
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

# -------------------------------
# ROOT CHECK (OPTIONAL)
# -------------------------------
@app.get("/")
def home():
    return {"message": "Backend is running 🚀"}

# -------------------------------
# RUN
# -------------------------------
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)