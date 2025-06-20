# Security Hardening Cookbook

## Overview
Collection of Kubernetes & CI/CD security best-practices packaged as ready-to-apply policies, scans, and pipelines. Focus areas: image hygiene, network segmentation, secrets handling, and compliance evidence.

## Why it matters
Orbis clients face audits (HIPAA, SOC-2) and production incidents caused by lax defaults (e.g., :latest images, public S3). This cookbook turns tribal knowledge into automatable guard-rails.

## Tech Stack
* OPA Gatekeeper (constraint templates)
* Trivy vulnerability & secret scanning
* Kubernetes NetworkPolicies
* GitHub Actions security workflow
* Kyverno optional alternative

## Task Checklist
- [ ] OPA Gatekeeper install manifests  
- [ ] ConstraintTemplates + Constraints:
  - [ ] Deny `image:latest`  
  - [ ] Require CPU/memory limits  
  - [ ] Block public LoadBalancers  
- [ ] NetworkPolicy examples (deny-all + allow namespace-scoped)  
- [ ] GitHub Action: Trivy scan pull-requests & image builds  
- [ ] Trivy filesystem & secret scan steps  
- [ ] README section: how to integrate with Argo CD sync-waves  
- [ ] Alerting via Slack on policy violation  
- [ ] CIS-benchmark scorecard script  

## Quick Start
```bash
kubectl apply -f manifests/gatekeeper.yaml
kubectl apply -f policies/  # loads constraints
# push PR and watch Trivy gate the build
```

---
*Status*: concept 