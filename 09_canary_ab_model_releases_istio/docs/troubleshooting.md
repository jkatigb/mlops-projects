# Troubleshooting Guide

## Common Issues and Solutions

### 1. Models Not Receiving Traffic

**Symptoms:**
- No metrics in Prometheus
- Traffic generation script shows all failures

**Solutions:**
```bash
# Check if Istio sidecar is injected
kubectl get pods -o yaml | grep istio-proxy

# If not, enable injection
kubectl label namespace default istio-injection=enabled
kubectl rollout restart deployment -n default

# Verify Istio configuration
istioctl analyze
```

### 2. Rollout Stuck at Analysis

**Symptoms:**
- Rollout paused indefinitely at analysis step
- No progression after configured duration

**Solutions:**
```bash
# Check analysis run status
kubectl get analysisrun

# View analysis details
kubectl describe analysisrun <name>

# Check Prometheus connectivity
kubectl exec -n istio-system deployment/prometheus -- wget -qO- http://localhost:9090/-/healthy

# Verify metrics exist
kubectl exec -n istio-system deployment/prometheus -- \
  wget -qO- 'http://localhost:9090/api/v1/query?query=istio_request_total'
```

### 3. High Error Rates

**Symptoms:**
- Success rate below threshold
- Rollout automatically aborted

**Solutions:**
```bash
# Check pod logs
kubectl logs -l app=iris-model,version=v2 -c classifier

# Verify model artifacts are accessible
kubectl describe pod -l app=iris-model,version=v2

# Test endpoint directly
kubectl exec -it deployment/iris-model-v2 -- curl localhost:9000/health/live
```

### 4. Grafana Dashboard Not Showing Data

**Symptoms:**
- Empty panels in Grafana
- "No data" errors

**Solutions:**
```bash
# Import dashboard with correct datasource
# 1. Access Grafana UI
kubectl port-forward -n istio-system svc/grafana 3000:3000

# 2. Go to Dashboards → Import
# 3. Upload grafana/dashboard.json
# 4. Select "Prometheus" as datasource

# Verify Prometheus is configured in Grafana
# Settings → Data Sources → Prometheus
# URL should be: http://prometheus:9090
```

### 5. Virtual Service Not Working

**Symptoms:**
- Traffic not splitting according to weights
- All traffic going to one version

**Solutions:**
```bash
# Check VirtualService configuration
kubectl get virtualservice iris-model -o yaml

# Verify service exists
kubectl get svc iris-model

# Check endpoint readiness
kubectl get endpoints iris-model

# Test with specific headers
curl -H "x-version: v2" http://iris-model/api/v1.0/predictions
```

## Debugging Commands

### Check Istio Configuration
```bash
# Validate all Istio resources
istioctl analyze

# Check proxy configuration
istioctl proxy-config cluster -n default deployment/iris-model-v1

# View routes
istioctl proxy-config route -n default deployment/iris-model-v1
```

### Monitor Rollout Progress
```bash
# Watch rollout status
kubectl argo rollouts get rollout iris-rollout --watch

# View rollout events
kubectl describe rollout iris-rollout

# Check analysis runs
kubectl get analysisrun -w
```

### Verify Metrics
```bash
# Query Prometheus directly
curl http://localhost:9090/api/v1/query?query=iris:success_rate:5m

# Check recording rules
kubectl get prometheusrule -n istio-system iris-model-rules -o yaml
```

## Performance Tuning

### 1. Increase Replicas
```yaml
spec:
  replicas: 5  # Increase for higher throughput
```

### 2. Adjust Resource Limits
```yaml
resources:
  requests:
    cpu: 500m
    memory: 1Gi
  limits:
    cpu: 2
    memory: 2Gi
```

### 3. Configure HPA
```bash
kubectl autoscale deployment iris-model-v1 --min=2 --max=10 --cpu-percent=70
```

## Emergency Procedures

### Immediate Rollback
```bash
# Abort current rollout
kubectl argo rollouts abort iris-rollout

# Force all traffic to v1
kubectl patch virtualservice iris-model --type merge -p '
spec:
  http:
  - route:
    - destination:
        host: iris-model
        subset: v1
      weight: 100'
```

### Complete Reset
```bash
# Run cleanup script
./cleanup.sh

# Restart from scratch
./setup.sh
./deploy.sh
```