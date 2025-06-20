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
- [x] Helm install LitmusChaos in `chaos` namespace
- [x] Create experiments:
  - [x] `pod-delete` on training job
  - [x] `aws-s3-object-corruption`
  - [x] `network-latency` on inference service
- [x] Define steady-state hypothesis metrics
- [x] Grafana dashboard for experiment results
- [x] Argo Rollouts strategy with max surge/unavailable
- [x] GitHub Action to run chaos tests nightly
- [x] README: how to interpret results & revert state

## Usage
### Install LitmusChaos
```bash
./install_litmus_helm.sh
```

### Run experiments
```bash
kubectl apply -f experiments/pod-delete.yaml
kubectl apply -f experiments/aws-s3-object-corruption.yaml
kubectl apply -f experiments/network-latency.yaml
```

Monitor progress using:
```bash
watch kubectl get chaosresults -n chaos
```

### Cleanup
```bash
kubectl delete chaosengine --all -n chaos
```

---
*Status*: alpha
