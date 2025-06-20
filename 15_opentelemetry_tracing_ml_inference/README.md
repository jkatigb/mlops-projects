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
# Start all services
docker compose up --build

# Test the API
curl -X POST localhost:8000/predict -H "Content-Type: application/json" -d '{"feature": 1.2}'

# Health check
curl localhost:8000/health

# View traces in Jaeger UI
open http://localhost:16686

# Generate load for testing
python load_test.py --url http://localhost:8000
```

## Using Tempo Instead of Jaeger
```bash
# Run with Tempo profile
docker compose --profile tempo up --build

# Tempo API is available at http://localhost:3200
```

## Viewing Traces
1. Open Jaeger UI at http://localhost:16686
2. Select "ml-inference-api" from the Service dropdown
3. Click "Find Traces"
4. Click on any trace to see the waterfall view showing:
   - API request handling
   - Database query execution
   - External HTTP call
   - Model inference timing

---
*Status*: ready
