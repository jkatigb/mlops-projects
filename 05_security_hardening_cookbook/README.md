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
- [x] OPA Gatekeeper install manifests
- [x] ConstraintTemplates + Constraints:
  - [x] Deny `image:latest`
  - [x] Require CPU/memory limits
  - [x] Block public LoadBalancers
- [x] NetworkPolicy examples (deny-all + allow namespace-scoped)
- [x] GitHub Action: Trivy scan pull-requests & image builds
- [x] Trivy filesystem & secret scan steps
- [x] README section: how to integrate with Argo CD sync-waves
- [x] Alerting via Slack on policy violation
- [x] CIS-benchmark scorecard script

## Quick Start
```bash
kubectl apply -f manifests/gatekeeper.yaml
kubectl apply -f policies/  # loads constraints
kubectl apply -f networkpolicies/
# push PR and watch Trivy gate the build
```

## Argo CD Integration
Add the policies repo as an application and set a lower `sync-wave` so Gatekeeper deploys before workloads:
```yaml
metadata:
  annotations:
    argocd.argoproj.io/sync-wave: "0"
```
This ensures constraints are active before your deployments run.

## Slack Alerting
Policy violations in GitHub Actions trigger a Slack notification using `rtCamp/action-slack-notify`. Configure the `SLACK_WEBHOOK` secret in your repository.

## CIS Benchmark Scorecard
Run the helper script to generate a kube-bench report summary:
```bash
bash scripts/cis_scorecard.sh > scorecard.txt
```
The resulting `scorecard.txt` can be shared with auditors as evidence.

---
