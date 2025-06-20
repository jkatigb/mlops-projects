# Canary & A/B Model Releases with Istio

## Overview
Showcases progressive delivery of ML models using Seldon Core (or KFServing) with Istio traffic splitting. Automates rollback if business KPI or latency degrades.

## Why it matters
Teams often replace models in a "big-bang" manner, risking customer impact. Canarying reduces blast radius and enables data-driven promotion decisions.

## Tech Stack
* K8s + Istio service mesh
* Seldon Core or KFServing
* Prometheus adapter for custom metrics
* Argo Rollouts (optional) or Seldon inbuilt canary
* Grafana & Alertmanager

## Task Checklist
- [ ] Install Istio with `istioctl install --set profile=demo`  
- [ ] Deploy baseline model (`v1`) via SeldonDeployment  
- [ ] Deploy new model (`v2`) and create `VirtualService` traffic split 90/10  
- [ ] Load test script to generate requests & metrics  
- [ ] Prometheus recording rules for accuracy / latency KPI  
- [ ] Alertmanager + Argo Rollouts analysis template for automated rollback  
- [ ] Gradually shift traffic 90/10 → 50/50 → 0/100  
- [ ] Grafana dashboard to visualise metrics per version  
- [ ] Documentation of manual override / abort  

## Demo Flow
```bash
kubectl apply -f deploy/v1.yaml  # baseline
kubectl apply -f deploy/v2.yaml  # new model
python scripts/traffic_gen.py --rps 20
# watch Grafana & observe rollout progression
```

---
*Status*: planning 