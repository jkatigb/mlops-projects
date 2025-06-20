from fastapi import FastAPI
from pydantic import BaseModel
from prometheus_fastapi_instrumentator import Instrumentator
import random

app = FastAPI(title="Model Drift Demo")

Instrumentator().instrument(app).expose(app)

class PredictRequest(BaseModel):
    feature: float

class PredictResponse(BaseModel):
    prediction: float

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/predict", response_model=PredictResponse)
def predict(req: PredictRequest):
    # trivial mock model: multiply feature then add noise
    pred = req.feature * 0.5 + random.random()
    return {"prediction": pred}
