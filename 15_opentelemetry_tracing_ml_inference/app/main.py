import asyncio
import random
from fastapi import FastAPI
from pydantic import BaseModel
from .db import engine, fetch_feature
from .external import call_external
from .tracing import setup_tracing
from opentelemetry import trace

app = FastAPI(title="ML Inference Service")


class PredictionRequest(BaseModel):
    feature: float


@app.on_event("startup")
async def startup() -> None:
    setup_tracing(app, engine)


@app.post("/predict")
async def predict(req: PredictionRequest) -> dict:
    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span("model-inference") as span:
        span.set_attribute("model.name", "demo-model")
        span.set_attribute("model.version", "1.0")
        span.set_attribute("input.size", req.feature)

        db_val = await fetch_feature(req.feature)
        await call_external()
        await asyncio.sleep(random.uniform(0.05, 0.3))
        prediction = db_val * 0.42
        return {"prediction": prediction}
