# Self-Service JupyterHub on EKS

## Overview
Deploys JupyterHub via Helm on AWS EKS with per-user IAM roles and idle-cull automation. DS teams get secure, cost-controlled notebooks that integrate with existing S3 data lakes.

## Why it matters
Unmanaged notebooks consume GPUs and leak credentials. Providing a governed, ephemeral environment boosts productivity while slashing infra waste.

## Tech Stack
* AWS EKS + IAM Roles for ServiceAccounts (IRSA)
* JupyterHub Helm chart (Zero to JupyterHub)
* Karpenter optional for autoscaling nodes
* Idle-cull & resource quotas
* Terraform for infra

## Task Checklist
- [ ] Terraform: VPC, EKS, OIDC provider, IAM policies for S3  
- [ ] Helm values:
  - [ ] SingleUser profile with GPU & CPU options  
  - [ ] HUB image with LDAP/OIDC auth (Cognito or Okta)  
  - [ ] Idle culler >30 min inactivity  
- [ ] IRSA annotations for per-user S3 access  
- [ ] Pre-configured Conda environments via `repo2docker`  
- [ ] Docs: how to add new environment via Git PR  
- [ ] Grafana dashboard: active users vs. node utilisation  
- [ ] Cost guardrails: PodDisruptionBudget & shutdown window  

## Quick Demo
```bash
make infra-up
helm upgrade --install jhub jupyterhub/jupyterhub -f helm/values.yaml
open https://jupyter.$DOMAIN  # login with test@orbis.dev
```

---
*Status*: skeleton 