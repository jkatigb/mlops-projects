#!/bin/bash

set -e

echo "=== Setting up Istio Canary Rollout Demo ==="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check prerequisites
check_command() {
    if ! command -v $1 &> /dev/null; then
        echo -e "${RED}Error: $1 is not installed${NC}"
        exit 1
    fi
}

echo "Checking prerequisites..."
check_command kubectl
check_command istioctl
check_command helm

# Check if Istio is installed
if ! kubectl get namespace istio-system &> /dev/null; then
    echo -e "${YELLOW}Istio not found. Installing Istio...${NC}"
    istioctl install --set profile=demo -y
    
    # Enable istio injection for default namespace
    kubectl label namespace default istio-injection=enabled --overwrite
else
    echo -e "${GREEN}Istio is already installed${NC}"
fi

# Install Prometheus if not present
if ! kubectl get deployment prometheus -n istio-system &> /dev/null; then
    echo -e "${YELLOW}Installing Prometheus addon...${NC}"
    kubectl apply -f https://raw.githubusercontent.com/istio/istio/release-1.19/samples/addons/prometheus.yaml
fi

# Install Grafana if not present
if ! kubectl get deployment grafana -n istio-system &> /dev/null; then
    echo -e "${YELLOW}Installing Grafana addon...${NC}"
    kubectl apply -f https://raw.githubusercontent.com/istio/istio/release-1.19/samples/addons/grafana.yaml
fi

# Install Argo Rollouts
if ! kubectl get namespace argo-rollouts &> /dev/null; then
    echo -e "${YELLOW}Installing Argo Rollouts...${NC}"
    kubectl create namespace argo-rollouts
    kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/install.yaml
else
    echo -e "${GREEN}Argo Rollouts is already installed${NC}"
fi

# Install Seldon Core
if ! kubectl get namespace seldon-system &> /dev/null; then
    echo -e "${YELLOW}Installing Seldon Core...${NC}"
    kubectl create namespace seldon-system
    helm repo add seldon https://storage.googleapis.com/seldon-charts
    helm repo update
    helm install seldon-core seldon/seldon-core-operator \
        --namespace seldon-system \
        --set usageMetrics.enabled=false \
        --set istio.enabled=true
else
    echo -e "${GREEN}Seldon Core is already installed${NC}"
fi

# Wait for all components to be ready
echo "Waiting for all components to be ready..."
kubectl wait --for=condition=ready pod -l app=prometheus -n istio-system --timeout=300s
kubectl wait --for=condition=ready pod -l app=grafana -n istio-system --timeout=300s
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=argo-rollouts -n argo-rollouts --timeout=300s
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=seldon-core-operator -n seldon-system --timeout=300s

echo -e "${GREEN}✓ All components are ready!${NC}"
echo ""
echo "Next steps:"
echo "1. Run './deploy.sh' to deploy the canary rollout demo"
echo "2. Run 'kubectl port-forward -n istio-system svc/grafana 3000:3000' to access Grafana"
echo "3. Import the dashboard from grafana/dashboard.json"