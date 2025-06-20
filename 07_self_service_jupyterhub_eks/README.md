# Self-Service JupyterHub on EKS

## Overview
Deploys JupyterHub via Helm on AWS EKS with per-user IAM roles and idle-culling. Data scientists get secure notebooks backed by S3 and GPU/CPU profiles.

## Why it matters
Unmanaged notebooks consume GPUs and leak credentials. Providing a governed, ephemeral environment boosts productivity while slashing infra waste.

## Tech Stack
* AWS EKS + IAM Roles for ServiceAccounts (IRSA)
* Terraform modules for VPC, EKS and IAM
* JupyterHub Helm chart (Zero to JupyterHub)
* Karpenter optional for autoscaling nodes
* Prometheus + Grafana for metrics

## Contents
* `terraform/` – infrastructure modules
* `helm/values.yaml` – JupyterHub configuration
* `examples/repo2docker/` – sample environments
* `docs/` – how-to guides

## Quick Demo
```bash
cd terraform && terraform init && terraform apply -auto-approve
helm repo add jupyterhub https://jupyterhub.github.io/helm-chart/
helm upgrade --install jhub jupyterhub/jupyterhub -n jhub \
  --create-namespace -f ../helm/values.yaml
```

After a few minutes open the ELB URL and authenticate.

---
*Status*: alpha

