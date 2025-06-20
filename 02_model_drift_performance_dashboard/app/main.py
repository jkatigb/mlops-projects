from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, validator
from prometheus_fastapi_instrumentator import Instrumentator
import random
import math
import logging
import os

# Optional seed for reproducible behavior in demos
if seed := os.getenv("RANDOM_SEED"):
    random.seed(int(seed))

app = FastAPI(title="Model Drift Demo")
logger = logging.getLogger(__name__)

Instrumentator().instrument(app).expose(app)

class PredictRequest(BaseModel):
    feature: float
    
    @validator('feature')
    def validate_feature(cls, v):
        if not math.isfinite(v):
            raise ValueError('Feature must be a finite number')
        return v

class PredictResponse(BaseModel):
    prediction: float

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/predict", response_model=PredictResponse)
def predict(req: PredictRequest):
    try:
        # trivial mock model: multiply feature then add noise
        pred = req.feature * 0.5 + random.random()
        
        # Ensure prediction is finite
        if not math.isfinite(pred):
            raise HTTPException(status_code=500, detail="Model produced invalid prediction")
            
        return {"prediction": pred}
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
