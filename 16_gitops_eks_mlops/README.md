# GitOps EKS ML Pipeline

## Overview
This example provisions an opinionated AWS EKS environment with Terraform and deploys
MLflow, Argo CD, Prometheus/Grafana and Karpenter via Helm. A GitHub Actions
workflow trains a toy model, builds an inference image, pushes to ECR and
updates Kubernetes manifests so Argo CD can promote the release from `staging`
to `prod`.

## Directory Structure
- `terraform/` – infrastructure as code modules
- `helm/` – Helm charts or manifest snippets for cluster services
- `k8s/` – sample Kubernetes manifests
- `.github/workflows/` – CI/CD pipeline
- `grafana/` – dashboards and alert rules
- `scripts/` – helper scripts
- `docs/architecture.png` – high level architecture

## Quick Start
```bash
make deploy        # terraform apply + helm installs
make destroy       # teardown
```
After the cluster is ready trigger the pipeline:
```bash
gh workflow run train-and-deploy.yml
```

## Demo Instructions
1. Run `make deploy` and wait for Argo CD to sync apps.
2. Execute the GitHub Actions workflow above.
3. Inspect MLflow UI and Grafana dashboards via the LoadBalancer URLs output by Terraform.
4. Promote from staging to prod by merging the auto-generated PR.

---
*Status*: minimal working skeleton
