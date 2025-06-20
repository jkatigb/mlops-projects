# Cost-Aware GPU Auto-Scaler PoC

## Overview
Demonstrates dynamic provisioning of spot GPU nodes **only when** ML workloads need them, and automatic termination when idle. Achieved with Karpenter's flexible provisioning policies and CloudWatch metrics for cost visibility.

## Why it matters
GPU instances are expensive. Many data science teams leave them running 24/7. Automating scale-to-zero can cut training/inference costs by >40 %.

## Tech Stack
* AWS EKS
* Karpenter (provisioner + spot interruption handling)
* CloudWatch + Grafana for cost & utilisation dashboards
* Sample PyTorch training job (K8s CronJob)

## Task Checklist
- [x] Terraform: VPC, EKS, IAM roles for Karpenter
- [x] Helm install for Karpenter controller
- [x] Karpenter `Provisioner` manifest:
  - [x] Restrict to GPU instance families
  - [x] Prefer spot capacity with `capacityType=spot`
  - [x] TTL-after-empty = 60s
- [x] Example `Job` (on-demand training) triggering GPU need
- [x] CloudWatch metric filters for EC2 cost per namespace
- [x] Grafana dashboard JSON
- [ ] Simulate workload queue: `kubectl create job ...`
- [x] Document spot interruption handling & job checkpointing
- [x] Cost comparison spreadsheet (on-demand vs auto-scaled)

## Demo Script
```bash
make infra-up          # terraform apply
kubectl apply -f jobs/train-mnist.yaml
watch kubectl get nodes  # observe GPU node appear
# wait for job completion
watch kubectl get nodes  # node should disappear within 1–2 minutes
open http://grafana.$DOMAIN/d/gpu-cost
```

---
*Status*: complete 
