import asyncio
import random
from typing import Dict

from fastapi import FastAPI
from pydantic import BaseModel
from opentelemetry import trace

from .db import engine, fetch_feature
from .external import call_external
from .tracing import setup_tracing

app = FastAPI(title="ML Inference Service")


class PredictionRequest(BaseModel):
    feature: float


@app.on_event("startup")
async def startup() -> None:
    setup_tracing(app, engine)


@app.get("/health")
async def health() -> Dict[str, str]:
    return {"status": "healthy"}


@app.post("/predict")
async def predict(req: PredictionRequest) -> Dict[str, float]:
    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span("model-inference") as span:
        span.set_attribute("model.name", "demo-model")
        span.set_attribute("model.version", "1.0")
        span.set_attribute("input.size", req.feature)

        try:
            db_val = await fetch_feature(req.feature)
            await call_external()
            await asyncio.sleep(random.uniform(0.05, 0.3))
            prediction = db_val * 0.42
            span.set_attribute("prediction.value", prediction)
            return {"prediction": prediction}
        except Exception as e:
            span.record_exception(e)
            span.set_status(trace.Status(trace.StatusCode.ERROR))
            raise
