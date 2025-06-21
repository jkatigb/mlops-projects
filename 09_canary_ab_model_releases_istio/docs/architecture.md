# Canary Rollout Architecture

## Overview

This demo showcases progressive delivery of ML models using:
- **Istio** for traffic management
- **Seldon Core** for model serving
- **Argo Rollouts** for canary deployment
- **Prometheus** for metrics collection
- **Grafana** for visualization

## Architecture Components

### 1. Model Serving Layer
- **Seldon Core** manages ML model deployments
- Two model versions (v1 and v2) run simultaneously
- Each version has its own Kubernetes deployment with replicas for HA

### 2. Traffic Management
- **Istio VirtualService** controls traffic splitting between versions
- **DestinationRule** defines subsets based on version labels
- Supports header-based routing for testing specific versions

### 3. Progressive Delivery
- **Argo Rollouts** manages the canary deployment process
- Automated promotion based on success rate metrics
- Configurable rollout steps: 10% → 50% → 100%

### 4. Monitoring & Analysis
- **Prometheus** collects Istio metrics
- Recording rules calculate success rates and latencies
- **AnalysisTemplate** defines success criteria for automated decisions

## Traffic Flow

```
Client Request
    ↓
Istio Gateway
    ↓
VirtualService (traffic split)
    ↓
DestinationRule
    ├─→ Subset v1 (90%)
    └─→ Subset v2 (10%)
         ↓
    Seldon Deployments
         ↓
    Model Containers
```

## Rollout Process

1. **Initial State**: 100% traffic to v1
2. **Canary Stage 1**: 10% to v2, 90% to v1
   - Analysis runs for 3 minutes
   - Checks success rate ≥ 95%
3. **Canary Stage 2**: 50% to v2, 50% to v1
   - Analysis runs again
   - Validates performance metrics
4. **Full Rollout**: 100% to v2
   - v1 can be kept for rollback

## Key Features

### Automated Rollback
- If success rate drops below 95%, rollout automatically aborts
- Traffic reverts to stable version (v1)
- Alerts sent to operations team

### Manual Controls
- Pause/resume rollout at any stage
- Force promotion or abort
- Real-time monitoring via dashboard

### Production Considerations

1. **Resource Management**
   - CPU/memory limits prevent resource exhaustion
   - Horizontal pod autoscaling for load handling

2. **Network Resilience**
   - Connection pooling limits
   - Outlier detection removes unhealthy instances
   - Retry policies for transient failures

3. **Observability**
   - Distributed tracing with Jaeger
   - Custom metrics for model performance
   - Centralized logging with Fluentd

## Security Best Practices

1. **Network Policies**
   - Restrict traffic between namespaces
   - Allow only required ingress/egress

2. **mTLS**
   - Istio automatically encrypts service-to-service communication
   - Certificate rotation handled by Istio

3. **RBAC**
   - Limit access to rollout controls
   - Audit logs for all changes