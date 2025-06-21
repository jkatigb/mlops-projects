# Reusable Helm Chart for Model Serving

## Overview
Opinionated Helm chart that wraps KFServing/Seldon plus best-practice defaults (HPA, GPU toggle, Prometheus annotations, secret injection). One `values.yaml` lets teams deploy any containerised model in <60 s.

## Why it matters
Copy-pasting YAML across projects leads to drift and mistakes. A reusable chart standardises rollout, metrics, and security.

## Tech Stack
* Helm 3
* Kubernetes Custom Resources (SeldonDeployment)
* Prometheus ServiceMonitor
* HorizontalPodAutoscaler

## Task Checklist
- [x] Chart skeleton (`Chart.yaml`, `values.yaml`, `templates/`)
- [x] Template parameters:
  - [x] `image.repository`, `tag`, `resource.limits`
  - [x] `gpu.enabled` (nodeSelector + tolerations)
  - [x] `autoscaling.enabled`, `minReplicas`, `maxReplicas`, `targetCPU`
  - [x] `prometheus.scrape` annotations
  - [x] `service.type` (ClusterIP/LoadBalancer)
- [x] CI job to run `helm lint` + `helm template`
- [x] Example `values-fastapi.yaml` for toy model
- [x] README section on installing & upgrading

## Quick Start
```bash
helm repo add mlops https://yourbucket.github.io/charts
helm install iris mlops/model-serving -f examples/values-iris.yaml
```

## Install

Clone the repo and install the chart with the example values:

```bash
helm install my-model ./chart -f examples/values-fastapi.yaml
```

## Upgrade

Update the release with any configuration changes:

```bash
helm upgrade my-model ./chart -f examples/values-fastapi.yaml
```
