# Canary & A/B Model Releases with Istio

## Overview
Showcases progressive delivery of ML models using Seldon Core with Istio traffic splitting. Rollouts are monitored with Prometheus metrics and automatically rolled back via Argo Rollouts if KPIs degrade.

## Why it matters
Teams often replace models in a "big-bang" manner, risking customer impact. Canarying reduces blast radius and enables data-driven promotion decisions.

## Tech Stack
* K8s + Istio service mesh
* Seldon Core or KFServing
* Prometheus adapter for custom metrics
* Argo Rollouts + Alertmanager
* Grafana dashboards

## Task Checklist
* [x] Install Istio with `istioctl install --set profile=demo`
* [x] Deploy baseline model (`v1`) via SeldonDeployment
* [x] Deploy new model (`v2`) and create `VirtualService` traffic split 90/10
* [x] Load test script to generate requests & metrics
* [x] Prometheus recording rules for accuracy / latency KPI
* [x] Alertmanager + Argo Rollouts analysis template for automated rollback
* [x] Gradually shift traffic 90/10 → 50/50 → 0/100
* [x] Grafana dashboard to visualise metrics per version
* [x] Documentation of manual override / abort

## Demo Flow
```bash
kubectl apply -f deploy/v1.yaml  # baseline
kubectl apply -f deploy/v2.yaml  # new model
kubectl apply -f deploy/destination-rule.yaml
kubectl apply -f deploy/virtualservice.yaml
kubectl apply -f prometheus/recording-rules.yaml
kubectl apply -f argo/analysis-template.yaml
kubectl apply -f argo/rollout.yaml
python scripts/traffic_gen.py --rps 20
```
See [docs/manual_override.md](docs/manual_override.md) for manual promotion or abort commands.

---
*Status*: completed
