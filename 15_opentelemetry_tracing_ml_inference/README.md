# OpenTelemetry Tracing for ML Inference

## Overview
End-to-end distributed tracing of an ML inference request using OpenTelemetry SDK. Trace spans cover API gateway → FastAPI model server → feature store DB → external service call. Visualised in Jaeger.

## Why it matters
Latency spikes are hard to debug without request-level visibility. Tracing pinpoints slow components (e.g., DB query, model load) and informs optimisation.

## Tech Stack
* FastAPI + OpenTelemetry Python SDK
* Jaeger (all-in-one) or Tempo
* Prometheus metrics side-car
* Docker-compose & Helm charts

## Task Checklist
- [ ] Instrument FastAPI routes with `opentelemetry-instrumentation-fastapi`  
- [ ] Add span attributes for model name, version, input size  
- [ ] Propagate context through async DB call (SQLAlchemy) and HTTP call  
- [ ] Export traces to Jaeger via OTLP  
- [ ] Docker-compose: api, jaeger, db  
- [ ] Load test script to generate traffic with variable latency  
- [ ] Grafana Tempo alternative config  
- [ ] README: screenshot of trace waterfall  

## Quick Run
```bash
docker compose up --build
curl -X POST localhost:8000/predict -d '{"feature": 1.2}'
open http://localhost:16686  # Jaeger UI
```

---
*Status*: draft 