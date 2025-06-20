# Model Drift & Performance Dashboard

## Overview
Proof-of-concept service that detects model drift and latency anomalies in real time. Combines Prometheus metrics, Evidently.ai statistical checks, and Grafana/Alertmanager to surface issues via Slack.

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
- [ ] Scaffold FastAPI server with `/predict` and `/health` endpoints  
- [ ] Instrument request/response latency & throughput via `prometheus_fastapi_instrumentator`  
- [ ] Capture predictions + ground-truth (simulated) to feed Evidently  
- [ ] Batch job / side-car that runs Evidently drift reports every N minutes  
- [ ] Expose drift metrics to Prometheus  
- [ ] Grafana dashboard panels:
  - [ ] p50/p95 latency  
  - [ ] Drift score over time  
  - [ ] Error rate  
- [ ] Alertmanager rules: high latency, significant drift, high error-rate  
- [ ] Slack incoming webhook integration  
- [ ] Docker-compose and Helm charts for local vs. k8s deploy  
- [ ] README demo script with sample traffic generator

## Quick Demo
```bash
docker compose up --build  # spins up API, Prometheus, Grafana
python scripts/generate_traffic.py --mode good
python scripts/generate_traffic.py --mode drift   # triggers drift alert
open http://localhost:3000  # Grafana UI
```

Use the Slack channel configured in `.env` to view alerts.

---
*Status*: planning 