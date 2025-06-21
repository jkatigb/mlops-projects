#!/bin/bash

set -e

echo "=== Deploying Canary Rollout Demo ==="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Deploy Prometheus recording rules
echo "Applying Prometheus recording rules..."
kubectl apply -f prometheus/recording-rules.yaml

# Deploy analysis template
echo "Applying analysis template..."
kubectl apply -f argo/analysis-template.yaml

# Deploy baseline model (v1)
echo "Deploying baseline model (v1)..."
kubectl apply -f deploy/v1.yaml

# Wait for v1 to be ready
echo "Waiting for v1 deployment to be ready..."
kubectl wait --for=condition=ready pod -l app=iris-model,version=v1 --timeout=300s || true

# Deploy v2 model
echo "Deploying new model (v2)..."
kubectl apply -f deploy/v2.yaml

# Apply destination rule
echo "Applying destination rule..."
kubectl apply -f deploy/destination-rule.yaml

# Apply virtual service
echo "Applying virtual service..."
kubectl apply -f deploy/virtualservice.yaml

# Deploy rollout
echo "Deploying Argo Rollout..."
kubectl apply -f argo/rollout.yaml

echo -e "${GREEN}✓ Deployment complete!${NC}"
echo ""
echo "Monitor the rollout:"
echo "  kubectl argo rollouts get rollout iris-rollout --watch"
echo ""
echo "Generate traffic:"
echo "  python scripts/traffic_gen.py --rps 20 --duration 600"
echo ""
echo "View metrics in Grafana:"
echo "  kubectl port-forward -n istio-system svc/grafana 3000:3000"
echo ""
echo "Manual controls:"
echo "  kubectl argo rollouts promote iris-rollout    # Promote immediately"
echo "  kubectl argo rollouts abort iris-rollout      # Abort rollout"
echo "  kubectl argo rollouts pause iris-rollout      # Pause rollout"