# Chaos Engineering Suite for ML Pipelines

## Overview
Inject failures into ML training and serving components using LitmusChaos to validate auto-healing and rollback mechanisms (Argo Rollouts, Kubernetes restart policies, S3 versioning).

## Why it matters
Production ML systems must gracefully handle pod crashes, corrupted objects, and network partitions. Proving resilience increases stakeholder confidence and uncovers hidden bugs.

## Tech Stack
* LitmusChaos experiments
* Argo Rollouts (or native Deployments)
* Kubernetes
* Prometheus & Grafana

## Task Checklist
- [ ] Helm install LitmusChaos in `chaos` namespace  
- [ ] Create experiments:
  - [ ] `pod-delete` on training job  
  - [ ] `aws-s3-object-corruption`  
  - [ ] `network-latency` on inference service  
- [ ] Define steady-state hypothesis metrics  
- [ ] Grafana dashboard for experiment results  
- [ ] Argo Rollouts strategy with max surge/unavailable  
- [ ] GitHub Action to run chaos tests nightly  
- [ ] README: how to interpret results & revert state  

## Demo
```bash
kubectl apply -f experiments/pod-delete.yaml
watch kubectl get chaosresults -n litmus
```

---
*Status*: plan 