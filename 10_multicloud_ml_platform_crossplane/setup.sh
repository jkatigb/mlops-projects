#!/bin/bash

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    local missing=()
    
    for cmd in kubectl helm aws gcloud; do
        if ! command -v "$cmd" &> /dev/null; then
            missing+=("$cmd")
        fi
    done
    
    if [ ${#missing[@]} -ne 0 ]; then
        log_error "Missing required tools: ${missing[*]}"
        log_info "Please install missing tools and try again"
        exit 1
    fi
    
    log_info "All prerequisites satisfied"
}

# Create AWS credentials secret
create_aws_secret() {
    log_info "Creating AWS credentials secret..."
    
    if kubectl get secret aws-creds -n crossplane-system &>/dev/null; then
        log_warn "AWS credentials already exist, skipping"
        return
    fi
    
    # Check for AWS credentials
    if [ ! -f ~/.aws/credentials ]; then
        log_error "AWS credentials not found at ~/.aws/credentials"
        log_info "Please run 'aws configure' first"
        exit 1
    fi
    
    kubectl create namespace crossplane-system --dry-run=client -o yaml | kubectl apply -f -
    
    kubectl create secret generic aws-creds \
        -n crossplane-system \
        --from-file=creds="${HOME}/.aws/credentials" \
        --dry-run=client -o yaml | kubectl apply -f -
        
    log_info "AWS credentials secret created"
}

# Create GCP credentials secret
create_gcp_secret() {
    log_info "Creating GCP credentials secret..."
    
    if kubectl get secret gcp-creds -n crossplane-system &>/dev/null; then
        log_warn "GCP credentials already exist, skipping"
        return
    fi
    
    # Check for GCP credentials
    GCP_CREDS="${GOOGLE_APPLICATION_CREDENTIALS:-${HOME}/.config/gcloud/application_default_credentials.json}"
    
    if [ ! -f "$GCP_CREDS" ]; then
        log_error "GCP credentials not found"
        log_info "Please run 'gcloud auth application-default login' first"
        log_info "Or set GOOGLE_APPLICATION_CREDENTIALS to point to your service account key"
        exit 1
    fi
    
    kubectl create secret generic gcp-creds \
        -n crossplane-system \
        --from-file=creds="$GCP_CREDS" \
        --dry-run=client -o yaml | kubectl apply -f -
        
    log_info "GCP credentials secret created"
}

# Install ArgoCD
install_argocd() {
    log_info "Installing ArgoCD..."
    
    if kubectl get namespace argocd &>/dev/null; then
        log_warn "ArgoCD namespace already exists, skipping installation"
        return
    fi
    
    kubectl create namespace argocd
    kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
    
    log_info "Waiting for ArgoCD to be ready..."
    kubectl wait --for=condition=available --timeout=300s deployment/argocd-server -n argocd
    
    log_info "ArgoCD installed successfully"
    
    # Get initial admin password
    local password=$(kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d)
    echo -e "${BLUE}ArgoCD admin password: ${password}${NC}"
}

# Main setup flow
main() {
    echo -e "${BLUE}=== Crossplane Multi-Cloud Setup ===${NC}"
    
    check_prerequisites
    create_aws_secret
    create_gcp_secret
    install_argocd
    
    log_info "Running Crossplane installation..."
    make crossplane-up
    
    log_info "Deploying cluster definitions..."
    make deploy-clusters
    
    echo -e "${GREEN}✓ Setup complete!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Wait for clusters to provision (10-15 minutes)"
    echo "2. Check status: make check-clusters"
    echo "3. Deploy applications: make deploy-apps"
    echo "4. Test failover: make failover"
}

# Run main function
main "$@"