#!/usr/bin/env bash
set -euo pipefail

# Configuration
AWS_CLUSTER="${AWS_CLUSTER:-prod-us}"
GCP_CLUSTER="${GCP_CLUSTER:-prod-eu}"
NAMESPACE="${NAMESPACE:-inference}"
DEPLOYMENT="${DEPLOYMENT:-inference}"
TIMEOUT="${TIMEOUT:-300}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_context() {
    local context=$1
    if ! kubectl config get-contexts "$context" &>/dev/null; then
        log_error "Context '$context' not found in kubeconfig"
        return 1
    fi
}

# Pre-flight checks
log_info "Starting failover from $AWS_CLUSTER to $GCP_CLUSTER"

check_context "$AWS_CLUSTER" || exit 1
check_context "$GCP_CLUSTER" || exit 1

# Check GCP cluster health before failover
log_info "Verifying $GCP_CLUSTER is healthy..."
if ! kubectl --context "$GCP_CLUSTER" get nodes -o wide &>/dev/null; then
    log_error "Cannot connect to $GCP_CLUSTER. Aborting failover."
    exit 1
fi

# Get node count for AWS cluster
NODE_COUNT=$(kubectl --context "$AWS_CLUSTER" get nodes --no-headers | wc -l)
log_info "Found $NODE_COUNT nodes in $AWS_CLUSTER"

# Drain AWS nodes
log_warn "Draining all nodes in $AWS_CLUSTER..."
kubectl --context "$AWS_CLUSTER" get nodes -o name | while read -r node; do
    log_info "Draining $node..."
    kubectl --context "$AWS_CLUSTER" drain "$node" \
        --ignore-daemonsets \
        --delete-emptydir-data \
        --force \
        --grace-period=30 \
        --timeout="${TIMEOUT}s" || log_warn "Failed to drain $node"
done

# Verify AWS workloads are stopped
log_info "Verifying workloads are stopped on $AWS_CLUSTER..."
RUNNING_PODS=$(kubectl --context "$AWS_CLUSTER" get pods -n "$NAMESPACE" --field-selector=status.phase=Running --no-headers | wc -l)
if [ "$RUNNING_PODS" -gt 0 ]; then
    log_warn "Still have $RUNNING_PODS running pods in $AWS_CLUSTER"
fi

# Check service availability on GCP
log_info "Checking service availability on $GCP_CLUSTER..."
if kubectl --context "$GCP_CLUSTER" rollout status deployment/"$DEPLOYMENT" -n "$NAMESPACE" --timeout="${TIMEOUT}s"; then
    log_info "Deployment $DEPLOYMENT is healthy on $GCP_CLUSTER"
else
    log_error "Deployment $DEPLOYMENT is not healthy on $GCP_CLUSTER"
    exit 1
fi

# Get endpoint for testing
ENDPOINT=$(kubectl --context "$GCP_CLUSTER" get service "$DEPLOYMENT" -n "$NAMESPACE" -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "")
if [ -n "$ENDPOINT" ]; then
    log_info "Service endpoint on $GCP_CLUSTER: http://$ENDPOINT"
    
    # Test endpoint if curl is available
    if command -v curl &>/dev/null; then
        log_info "Testing endpoint health..."
        if curl -s -o /dev/null -w "%{http_code}" "http://$ENDPOINT/health" | grep -q "200"; then
            log_info "Endpoint is responding with 200 OK"
        else
            log_warn "Endpoint health check failed"
        fi
    fi
fi

log_info "Failover complete! Traffic should now route to $GCP_CLUSTER"
log_info "To restore $AWS_CLUSTER, uncordon the nodes:"
echo "kubectl --context $AWS_CLUSTER uncordon --all"

