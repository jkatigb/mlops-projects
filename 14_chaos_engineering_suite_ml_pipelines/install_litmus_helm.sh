#!/bin/bash
# Install LitmusChaos using Helm into the 'chaos' namespace
set -euo pipefail

echo "Installing LitmusChaos..."

# Check if helm is installed
if ! command -v helm &> /dev/null; then
    echo "Error: Helm is not installed. Please install Helm first."
    exit 1
fi

# Add LitmusChaos helm repo
echo "Adding LitmusChaos Helm repository..."
helm repo add litmuschaos https://litmuschaos.github.io/litmus-helm/
helm repo update

# Install LitmusChaos
echo "Installing LitmusChaos in the 'chaos' namespace..."
helm install litmus litmuschaos/litmus \
    --namespace chaos \
    --create-namespace \
    --set portal.frontend.service.type=ClusterIP \
    --wait

echo "LitmusChaos installation complete!"
echo "Verifying installation..."
kubectl get pods -n chaos

echo ""
echo "To access LitmusChaos portal (if using port-forward):"
echo "kubectl port-forward svc/litmusportal-frontend-service 9091:9091 -n chaos"
