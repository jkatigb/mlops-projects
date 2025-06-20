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
- [ ] Chart skeleton (`Chart.yaml`, `values.yaml`, `templates/`)  
- [ ] Template parameters:
  - [ ] `image.repository`, `tag`, `resource.limits`  
  - [ ] `gpu.enabled` (nodeSelector + tolerations)  
  - [ ] `autoscaling.enabled`, `minReplicas`, `maxReplicas`, `targetCPU`  
  - [ ] `prometheus.scrape` annotations  
  - [ ] `service.type` (ClusterIP/LoadBalancer)  
- [ ] CI job to run `helm lint` + `helm template`  
- [ ] Example `values-fastapi.yaml` for toy model  
- [ ] README section on installing & upgrading  

## Quick Start
```bash
helm repo add mlops https://yourbucket.github.io/charts
helm install iris mlops/model-serving -f examples/values-iris.yaml
``` 