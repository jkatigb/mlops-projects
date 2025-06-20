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

### Prerequisites
- Kubernetes cluster (1.16+)
- Helm 3.x installed
- kubectl configured to access your cluster
- Target applications deployed with appropriate labels

### Install LitmusChaos
```bash
./install_litmus_helm.sh
```

### Validate Installation
```bash
./validate_chaos.sh
```

### Configure AWS Credentials (for S3 experiments)
```bash
# Edit the secret template with your credentials
cp experiments/aws-secret-template.yaml experiments/aws-secret.yaml
# Edit experiments/aws-secret.yaml with your AWS credentials
kubectl apply -f experiments/aws-secret.yaml
```

### Run Experiments
```bash
# Pod deletion experiment
kubectl apply -f experiments/pod-delete.yaml

# AWS S3 object corruption (requires AWS secret)
kubectl apply -f experiments/aws-s3-object-corruption.yaml

# Network latency injection
kubectl apply -f experiments/network-latency.yaml
```

### Monitor Progress
```bash
# Watch experiment status
watch kubectl get chaosengine,chaosresults -n chaos

# View detailed results
kubectl describe chaosresult <result-name> -n chaos
```

### Analyze Results
1. Check Prometheus metrics for SLO violations
2. Review application logs for error handling
3. Verify auto-recovery mechanisms
4. Document any manual interventions needed

### Cleanup
```bash
# Delete all running experiments
kubectl delete chaosengine --all -n chaos

# Delete specific experiment
kubectl delete chaosengine <engine-name> -n chaos
```

## Experiment Details

### Pod Delete
- Targets: Training jobs
- Impact: Tests job restart and checkpointing
- Duration: 30 seconds
- Affected pods: 50%

### Network Latency
- Targets: Inference services
- Impact: Tests timeout and retry logic
- Latency: 2000ms
- Affected pods: 100%

### S3 Object Corruption
- Targets: ML data buckets
- Impact: Tests data validation and error handling
- Corruption rate: 10% of objects
- Requires: AWS credentials

---
*Status*: ready
