# Model Drift & Performance Dashboard

## Overview
Proof-of-concept service that detects model drift and latency anomalies in real
time. Combines Prometheus metrics, Evidently.ai statistical checks, and Grafana/
Alertmanager to surface issues via Slack.

## Why it matters
Models silently losing accuracy or slowing down cost revenue and trust. This dashboard gives stakeholders instant visibility and an automated alerting loop.

## Tech Stack
* FastAPI inference service (Python)
* Evidently.ai drift detection
* Prometheus + Alertmanager
* Grafana dashboards
* Docker / Kubernetes manifests
* Slack webhook for alerts

## Task Checklist
- [x] Scaffold FastAPI server with `/predict` and `/health` endpoints
- [x] Instrument request/response latency & throughput via `prometheus_fastapi_instrumentator`
- [x] Capture predictions + ground-truth (simulated) to feed Evidently
- [x] Batch job / side-car that runs Evidently drift reports every N minutes
- [x] Expose drift metrics to Prometheus
- [x] Grafana dashboard panels:
  - [x] p50/p95 latency
  - [x] Drift score over time
  - [x] Error rate
- [x] Alertmanager rules: high latency, significant drift, high error-rate
- [x] Slack incoming webhook integration
- [x] Docker-compose and Helm charts for local vs. k8s deploy
- [x] README demo script with sample traffic generator

## Quick Demo
```bash
docker compose up --build  # spins up API, Prometheus, Grafana
python scripts/generate_traffic.py --mode good
python scripts/generate_traffic.py --mode drift   # triggers drift alert
open http://localhost:3000  # Grafana UI
```

Use the Slack channel configured in `.env` to view alerts.
