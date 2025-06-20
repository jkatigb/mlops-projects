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
- [ ] Bootstrap management cluster (kind or EKS) with Crossplane  
- [ ] Create `ProviderConfig` for AWS & GCP credentials  
- [ ] CompositeResourceDefinition (XCluster) describing standard cluster  
- [ ] Claim two clusters: `prod-us`, `prod-eu`  
- [ ] Configure Argo CD with `ClusterSecretStore`  
- [ ] ApplicationSet generating identical app per cluster  
- [ ] CI workflow to run `kubectl crossplane build|push`  
- [ ] Cost comparison & notes on egress pricing  
- [ ] Failover script: drain AWS cluster, verify GKE still serves  

## Demo Script
```bash
make crossplane-up
kubectl get clusters  # should list prod-us, prod-eu
kubectl get applications -n argocd
kubectl exec curl ...  # call inference endpoint in both regions
```

---
*Status*: idea 