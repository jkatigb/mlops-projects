#!/bin/bash

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=== Testing Istio Canary Rollout ===${NC}"

# Function to test model endpoint
test_endpoint() {
    local version=$1
    local url="http://iris-model.default.svc.cluster.local/api/v1.0/predictions"
    local header=""
    
    if [ "$version" == "v2" ]; then
        header="-H 'x-version: v2'"
    fi
    
    echo -e "\nTesting $version endpoint..."
    
    # Create test payload
    payload='{"data": {"ndarray": [[5.1, 3.5, 1.4, 0.2]]}}'
    
    # Test from within the cluster
    kubectl run test-curl-$version --rm -i --restart=Never --image=curlimages/curl -- \
        sh -c "curl -X POST $url \
        -H 'Content-Type: application/json' \
        $header \
        -d '$payload' \
        -w '\nHTTP Status: %{http_code}\nResponse Time: %{time_total}s\n'"
}

# Test rollout status
echo -e "${YELLOW}Checking rollout status...${NC}"
kubectl argo rollouts status iris-rollout || echo "Rollout not found"

# Test Istio configuration
echo -e "\n${YELLOW}Checking Istio configuration...${NC}"
kubectl get virtualservice iris-model -o yaml | grep -A 10 "weight:" || echo "VirtualService not configured"

# Test both model versions
echo -e "\n${YELLOW}Testing model endpoints...${NC}"
test_endpoint "v1"
test_endpoint "v2"

# Check Prometheus metrics
echo -e "\n${YELLOW}Checking Prometheus metrics...${NC}"
kubectl exec -n istio-system deployment/prometheus -- \
    wget -q -O- 'http://localhost:9090/api/v1/query?query=up{job="kubernetes-pods",namespace="default"}' \
    | jq '.data.result[] | select(.metric.pod_name | contains("iris-model"))' || echo "Metrics not available"

# Show traffic distribution
echo -e "\n${YELLOW}Current traffic distribution:${NC}"
kubectl exec -n istio-system deployment/prometheus -- \
    wget -q -O- 'http://localhost:9090/api/v1/query?query=sum(rate(istio_request_total{destination_service_name="iris-model"}[1m])) by (destination_version)' \
    | jq -r '.data.result[] | "\(.metric.destination_version): \(.value[1])"' || echo "No traffic data available"

echo -e "\n${GREEN}✓ Testing complete!${NC}"