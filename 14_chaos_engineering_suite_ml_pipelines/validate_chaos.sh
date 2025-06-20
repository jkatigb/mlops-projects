#!/bin/bash
# Validate chaos experiments and check results
set -euo pipefail

echo "Validating Chaos Engineering setup..."

# Check if LitmusChaos is installed
echo "Checking LitmusChaos installation..."
if ! kubectl get ns chaos &> /dev/null; then
    echo "Error: chaos namespace not found. Please run ./install_litmus_helm.sh first"
    exit 1
fi

# Check LitmusChaos pods
echo "Checking LitmusChaos pods..."
kubectl get pods -n chaos

# Check service account
echo "Checking service account..."
if ! kubectl get sa litmus-admin -n chaos &> /dev/null; then
    echo "Warning: litmus-admin service account not found"
    echo "Creating service account..."
    kubectl create sa litmus-admin -n chaos
fi

# Check for target applications
echo ""
echo "Checking target applications..."
echo "Train job deployments:"
kubectl get deployments -l app=train-job -A || echo "No train-job deployments found"

echo ""
echo "Inference service deployments:"
kubectl get deployments -l app=inference-service -A || echo "No inference-service deployments found"

# Check chaos experiments
echo ""
echo "Available chaos experiments:"
kubectl get chaosexperiments -n chaos

# Check chaos results
echo ""
echo "Recent chaos results:"
kubectl get chaosresults -n chaos

echo ""
echo "Validation complete!"
echo ""
echo "To run a chaos experiment:"
echo "  kubectl apply -f experiments/pod-delete.yaml"
echo ""
echo "To check experiment status:"
echo "  kubectl get chaosengine -n chaos"
echo "  kubectl get chaosresults -n chaos"