# Multi-Cloud ML Platform with Crossplane

## Overview
Provisions AWS EKS **and** GCP GKE clusters declaratively via Crossplane, then syncs the same Argo CD application (model inference service) to both. Demonstrates portable GitOps across clouds with a single repo.

## Why it matters
Some organisations hedge cloud risk or need region-specific deployments. Crossplane lets infra teams standardise on Kubernetes APIs instead of cloud-specific IaC.

## Tech Stack
* Crossplane (installed on management cluster)
* AWS & GCP provider packages
* Argo CD ApplicationSets for multi-cluster sync
* Terraform (bootstrap only)
* Sample FastAPI model server

## Task Checklist
- [x] Bootstrap management cluster (kind or EKS) with Crossplane
- [x] Create `ProviderConfig` for AWS & GCP credentials
- [x] CompositeResourceDefinition (XCluster) describing standard cluster
- [x] Claim two clusters: `prod-us`, `prod-eu`
- [x] Configure Argo CD with `ClusterSecretStore`
- [x] ApplicationSet generating identical app per cluster
- [x] CI workflow to run `kubectl crossplane build|push`
- [x] Cost comparison & notes on egress pricing
- [x] Failover script: drain AWS cluster, verify GKE still serves

## Demo Script
```bash
make crossplane-up
kubectl get clusters  # should list prod-us, prod-eu
kubectl get applications -n argocd
kubectl exec curl ...  # call inference endpoint in both regions
./failover.sh         # simulate AWS outage
```

## Cost Analysis
See [cost-analysis.md](cost-analysis.md) for rough pricing details.

---
*Status*: draft

