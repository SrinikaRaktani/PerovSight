import numpy as np
import cv2
import base64
from io import BytesIO
from PIL import Image

def encode_image(img):
    buffer = BytesIO()
    Image.fromarray(img).save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode()

async def predict_image(file):

    contents = await file.read()
    npimg = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(npimg, cv2.IMREAD_GRAYSCALE)

    img = cv2.resize(img, (128, 128))
    img_norm = img / 255.0

    panel_mask = img_norm > 0.1
    defect_mask = (img_norm < 0.4) & panel_mask

    defect_percentage = (np.sum(defect_mask) / defect_mask.size) * 100

    # -------------------------------
    # Electrical estimation
    # -------------------------------
    voc = 0.6 * (1 - 0.5 * defect_percentage / 100)
    jsc = 5.0 * (1 - defect_percentage / 100)
    ff  = 0.75 * (1 - 0.3 * defect_percentage / 100)
    pce1  = voc * jsc * ff
    ideal_power=0.6*5.0*0.75
    pce = (pce1 / ideal_power)*100 

    # -------------------------------
    # 🔴 RED DEFECT HIGHLIGHT
    # -------------------------------
    img_color = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    img_color[defect_mask] = [0, 0, 255]  # RED (BGR)
    img_rgb = cv2.cvtColor(img_color, cv2.COLOR_BGR2RGB)

    # -------------------------------
    # CONDITION + COLOR (FIXED ✅)
    # -------------------------------
    if defect_percentage < 5:
        condition = "🟢 Healthy"
        color = "#00ff00"
    elif defect_percentage < 15:
        condition = "🟡 Minor Defect"
        color = "#ffff00"
    elif defect_percentage < 30:
        condition = "🟠 Moderate Defect"
        color = "#ff9800"
    elif defect_percentage < 50:
        condition = "🔴 Severe Defect"
        color = "#ff0000"
    else:
        condition = "⚫ Critical Damage"
        color = "#555555"

    # -------------------------------
    # RETURN
    # -------------------------------
    return {
        "defect_percentage": float(defect_percentage),
        "pce": float(pce),
        "voc": float(voc),
        "jsc": float(jsc),
        "ff": float(ff),
        "condition": condition,
        "condition_color": color,   # ✅ FIXED
        "original_image": encode_image(img),
        "defect_image": encode_image(img_rgb)
    }