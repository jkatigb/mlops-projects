# GitOps-First ML Pipeline Template

## Overview
End-to-end reference implementation that provisions cloud infrastructure and automates the entire ML lifecycle using GitOps principles. A single Git repo manages:

* Terraform to spin up an AWS EKS cluster
* Argo CD to continuously reconcile Kubernetes manifests
* MLflow for experiment tracking & model registry
* Karpenter for cost-efficient (GPU) node autoscaling
* GitHub Actions that train a toy Sklearn model, register it in MLflow, containerise it, push to ECR, and trigger Argo CD promotion to staging → prod

## Why it matters
Reproducibility, automated promotion, and auditable change management are top pain points for Orbis clients. This template demonstrates all three in <15 minutes.

## Tech Stack
* AWS EKS + ECR
* Terraform & Helm
* Argo CD (GitOps)
* MLflow Tracking & Registry (S3 + RDS backend)
* Karpenter (GPU/spot autoscaling)
* GitHub Actions CI/CD
* Prometheus + Grafana for metrics

## Task Checklist
- [ ] Terraform module for VPC, EKS, and supporting AWS resources  
- [ ] Helm charts / manifests for:
  - [ ] Argo CD  
  - [ ] MLflow (backend + S3 bucket + service)  
  - [ ] Prometheus & Grafana  
  - [ ] Karpenter controller + provisioner  
- [ ] GitHub Actions workflow:
  - [ ] Train toy model (`sklearn` iris)  
  - [ ] Log & register model in MLflow  
  - [ ] Build inference image with model artifact  
  - [ ] Push image to ECR  
  - [ ] Commit/update Kubernetes manifest (tagged image)  
  - [ ] Argo CD auto-sync deploys to **staging**  
  - [ ] Manual gate to promote to **prod**  
- [ ] Sample Kubernetes manifests (staging & prod namespaces)
- [ ] Grafana dashboard JSON & sample alerts
- [ ] Makefile / scripts for `terraform init|apply`, bootstrap Argo CD, and destroy
- [ ] Architecture diagram (`docs/architecture.png`)
- [ ] Loom/YouTube walkthrough link placeholder

## How to Demo
```bash
make deploy            # provisions infra & installs Argo CD
make bootstrap-metrics  # optional: Prometheus/Grafana stack
# open Argo CD UI to watch sync
# trigger end-to-end pipeline
gh workflow run train-and-deploy.yml
```

After the workflow completes, open the LoadBalancer URL for the inference service and query the health endpoint.

---
*Status*: scaffold only – PRs welcome! 