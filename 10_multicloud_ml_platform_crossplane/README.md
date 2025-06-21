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
* [x] Bootstrap management cluster (kind or EKS) with Crossplane
* [x] Create `ProviderConfig` for AWS & GCP credentials
* [x] CompositeResourceDefinition (XCluster) describing standard cluster
* [x] Claim two clusters: `prod-us`, `prod-eu`
* [x] Configure Argo CD with `ClusterSecretStore`
* [x] ApplicationSet generating identical app per cluster
* [x] CI workflow to run `kubectl crossplane build|push`
* [x] Cost comparison & notes on egress pricing
* [x] Failover script: drain AWS cluster, verify GKE still serves

## Demo Script

### Prerequisites
* kubectl configured with access to management cluster
* AWS and GCP credentials configured as secrets
* Argo CD installed in the management cluster

```bash
make crossplane-up
kubectl get clusters  # should list prod-us, prod-eu
kubectl get applications -n argocd
kubectl exec curl ...  # call inference endpoint in both regions
./failover.sh         # simulate AWS outage
```

## Cost Analysis
See [cost-analysis.md](cost-analysis.md) for rough pricing details.

## Quick Start

```bash
# 1. Run setup script (installs Crossplane, ArgoCD, creates secrets)
./setup.sh

# 2. Deploy clusters (takes 10-15 minutes)
make deploy-clusters

# 3. Check cluster status
make check-clusters

# 4. Deploy applications
make deploy-apps

# 5. Test endpoints
make test-endpoints
```

## Architecture

This project demonstrates:
* **Multi-cloud abstraction**: Single API (Kubernetes CRDs) for both AWS and GCP
* **GitOps deployment**: ArgoCD ApplicationSets deploy to all clusters automatically
* **Disaster recovery**: Automated failover between regions/clouds
* **Cost optimization**: Uses GKE Autopilot and EKS managed node groups

## Files

* `bootstrap/`: Crossplane installation and provider configurations
* `clusters/`: XRD definitions, compositions, and cluster claims
* `argocd/`: ApplicationSet for multi-cluster deployments
* `.github/workflows/`: CI for building/pushing Crossplane packages

---
*Status*: completed

