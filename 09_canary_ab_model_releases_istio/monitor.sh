#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

clear

echo -e "${BLUE}=== Istio Canary Rollout Monitor ===${NC}"
echo ""

# Function to get rollout status
get_rollout_status() {
    kubectl argo rollouts status iris-rollout 2>/dev/null || echo "Rollout not found"
}

# Function to get traffic split
get_traffic_split() {
    kubectl get virtualservice iris-model -o jsonpath='{.spec.http[0].route[*].weight}' 2>/dev/null || echo "VirtualService not found"
}

# Function to get success rate
get_success_rate() {
    kubectl exec -n istio-system deployment/prometheus -- \
        wget -q -O- 'http://localhost:9090/api/v1/query?query=sum(rate(istio_request_total{destination_service_name="iris-model",response_code=~"2.."}[1m]))/sum(rate(istio_request_total{destination_service_name="iris-model"}[1m]))' \
        2>/dev/null | jq -r '.data.result[0].value[1] // "N/A"' 2>/dev/null || echo "N/A"
}

# Main monitoring loop
while true; do
    clear
    echo -e "${BLUE}=== Istio Canary Rollout Monitor ===${NC}"
    echo -e "Time: $(date)"
    echo ""
    
    echo -e "${YELLOW}Rollout Status:${NC}"
    get_rollout_status
    echo ""
    
    echo -e "${YELLOW}Traffic Split (v1/v2):${NC}"
    get_traffic_split
    echo ""
    
    echo -e "${YELLOW}Overall Success Rate:${NC}"
    SUCCESS_RATE=$(get_success_rate)
    if [ "$SUCCESS_RATE" != "N/A" ]; then
        SUCCESS_PCT=$(echo "$SUCCESS_RATE * 100" | bc -l | xargs printf "%.2f")
        if (( $(echo "$SUCCESS_PCT >= 95" | bc -l) )); then
            echo -e "${GREEN}${SUCCESS_PCT}%${NC}"
        else
            echo -e "${RED}${SUCCESS_PCT}%${NC}"
        fi
    else
        echo "N/A"
    fi
    echo ""
    
    echo -e "${YELLOW}Recent Rollout Events:${NC}"
    kubectl describe rollout iris-rollout | grep -A 5 "Events:" | tail -n 5
    echo ""
    
    echo "Press Ctrl+C to exit. Refreshing in 5 seconds..."
    sleep 5
done