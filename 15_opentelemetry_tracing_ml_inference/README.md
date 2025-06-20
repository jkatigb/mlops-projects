# OpenTelemetry Tracing for ML Inference

## Overview
End-to-end distributed tracing of an ML inference request using OpenTelemetry SDK. Trace spans cover API gateway → FastAPI model server → feature store DB → external service call. Visualised in Jaeger or Tempo.

## Why it matters
Latency spikes are hard to debug without request-level visibility. Tracing pinpoints slow components (e.g., DB query, model load) and informs optimisation.

## Tech Stack
* FastAPI + OpenTelemetry Python SDK
* Jaeger (all-in-one) or Tempo
* Prometheus metrics side-car
* Docker-compose & Helm charts

## Task Checklist
- [x] Instrument FastAPI routes with `opentelemetry-instrumentation-fastapi`
- [x] Add span attributes for model name, version, input size
- [x] Propagate context through async DB call (SQLAlchemy) and HTTP call
- [x] Export traces to Jaeger via OTLP
- [x] Docker-compose: api, jaeger, db
- [x] Load test script to generate traffic with variable latency
- [x] Grafana Tempo alternative config
- [x] README: screenshot of trace waterfall (not included in repo)

## Quick Run
```bash
docker compose up --build
curl -X POST localhost:8000/predict -d '{"feature": 1.2}'
open http://localhost:16686  # Jaeger UI
```

---
*Status*: draft
