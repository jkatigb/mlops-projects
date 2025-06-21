#!/bin/bash

echo "=== Cleaning up Canary Rollout Demo ==="

# Delete rollout
kubectl delete rollout iris-rollout --ignore-not-found=true

# Delete Istio resources
kubectl delete virtualservice iris-model --ignore-not-found=true
kubectl delete destinationrule iris-model --ignore-not-found=true

# Delete Seldon deployments
kubectl delete seldondeployment iris-model-v1 iris-model-v2 --ignore-not-found=true

# Delete analysis template
kubectl delete analysistemplate iris-success-rate --ignore-not-found=true

# Delete Prometheus rules
kubectl delete -f prometheus/recording-rules.yaml --ignore-not-found=true

echo "✓ Cleanup complete!"