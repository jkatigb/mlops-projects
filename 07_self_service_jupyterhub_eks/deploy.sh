#!/bin/bash
set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check AWS CLI
    if ! command -v aws &> /dev/null; then
        print_error "AWS CLI not found. Please install: https://aws.amazon.com/cli/"
        exit 1
    fi
    
    # Check Terraform
    if ! command -v terraform &> /dev/null; then
        print_error "Terraform not found. Please install: https://www.terraform.io/downloads"
        exit 1
    fi
    
    # Check kubectl
    if ! command -v kubectl &> /dev/null; then
        print_error "kubectl not found. Please install: https://kubernetes.io/docs/tasks/tools/"
        exit 1
    fi
    
    # Check Helm
    if ! command -v helm &> /dev/null; then
        print_error "Helm not found. Please install: https://helm.sh/docs/intro/install/"
        exit 1
    fi
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        print_error "AWS credentials not configured. Run 'aws configure'"
        exit 1
    fi
    
    print_status "All prerequisites satisfied!"
}

# Deploy infrastructure
deploy_infrastructure() {
    print_status "Deploying AWS infrastructure..."
    
    cd terraform
    
    # Check if terraform.tfvars exists
    if [ ! -f terraform.tfvars ]; then
        print_warning "terraform.tfvars not found. Copying from example..."
        cp terraform.tfvars.example terraform.tfvars
        print_error "Please edit terraform/terraform.tfvars with your configuration"
        exit 1
    fi
    
    # Initialize Terraform
    print_status "Initializing Terraform..."
    terraform init
    
    # Plan deployment
    print_status "Planning infrastructure deployment..."
    terraform plan -out=tfplan
    
    # Apply deployment
    read -p "Do you want to apply this plan? (yes/no): " confirm
    if [[ $confirm == "yes" ]]; then
        terraform apply tfplan
    else
        print_warning "Deployment cancelled"
        exit 0
    fi
    
    # Get outputs
    CLUSTER_NAME=$(terraform output -raw cluster_name)
    REGION=$(terraform output -raw region)
    S3_BUCKET=$(terraform output -raw s3_bucket_name)
    
    cd ..
}

# Configure kubectl
configure_kubectl() {
    print_status "Configuring kubectl..."
    aws eks update-kubeconfig --region $REGION --name $CLUSTER_NAME
    
    # Verify connection
    if kubectl get nodes &> /dev/null; then
        print_status "Successfully connected to EKS cluster"
        kubectl get nodes
    else
        print_error "Failed to connect to EKS cluster"
        exit 1
    fi
}

# Install JupyterHub
install_jupyterhub() {
    print_status "Installing JupyterHub..."
    
    # Add Helm repository
    print_status "Adding JupyterHub Helm repository..."
    helm repo add jupyterhub https://jupyterhub.github.io/helm-chart/
    helm repo update
    
    # Update S3 bucket in values file
    if [ -f helm/jupyterhub-values.yaml ]; then
        print_status "Updating S3 bucket in Helm values..."
        sed -i.bak "s/your-jupyterhub-storage-bucket/$S3_BUCKET/g" helm/jupyterhub-values.yaml
    else
        print_error "helm/jupyterhub-values.yaml not found!"
        exit 1
    fi
    
    # Check if GitHub OAuth is configured
    if grep -q "YOUR_GITHUB_CLIENT_ID" helm/jupyterhub-values.yaml; then
        print_warning "GitHub OAuth not configured in helm/jupyterhub-values.yaml"
        print_warning "Please update the following fields:"
        print_warning "  - hub.config.GitHubOAuthenticator.client_id"
        print_warning "  - hub.config.GitHubOAuthenticator.client_secret"
        print_warning "  - hub.config.GitHubOAuthenticator.oauth_callback_url"
        print_warning "  - hub.config.GitHubOAuthenticator.allowed_organizations"
        read -p "Continue anyway? (yes/no): " confirm
        if [[ $confirm != "yes" ]]; then
            exit 1
        fi
    fi
    
    # Install JupyterHub
    print_status "Installing JupyterHub with Helm..."
    helm upgrade --install jupyterhub jupyterhub/jupyterhub \
        --namespace jupyterhub \
        --create-namespace \
        --values helm/jupyterhub-values.yaml \
        --version 3.3.7 \
        --wait \
        --timeout 10m
    
    print_status "JupyterHub installation complete!"
}

# Get JupyterHub URL
get_jupyterhub_url() {
    print_status "Getting JupyterHub URL..."
    
    # Wait for load balancer
    print_status "Waiting for load balancer to be ready..."
    kubectl wait --for=condition=ready --timeout=300s -n jupyterhub pod -l component=proxy
    
    # Get URL
    JUPYTERHUB_URL=$(kubectl get svc -n jupyterhub proxy-public -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
    
    if [ -z "$JUPYTERHUB_URL" ]; then
        print_warning "Load balancer URL not yet available. Try running:"
        print_warning "kubectl get svc -n jupyterhub proxy-public"
    else
        print_status "JupyterHub is available at: http://$JUPYTERHUB_URL"
    fi
}

# Main deployment flow
main() {
    print_status "Starting JupyterHub deployment..."
    
    check_prerequisites
    
    # Check if infrastructure already exists
    if [ -d terraform/.terraform ]; then
        cd terraform
        if terraform output cluster_name &> /dev/null; then
            print_warning "Infrastructure already exists"
            CLUSTER_NAME=$(terraform output -raw cluster_name)
            REGION=$(terraform output -raw region)
            S3_BUCKET=$(terraform output -raw s3_bucket_name)
            cd ..
            
            read -p "Skip infrastructure deployment? (yes/no): " skip_infra
            if [[ $skip_infra != "yes" ]]; then
                deploy_infrastructure
            fi
        else
            cd ..
            deploy_infrastructure
        fi
    else
        deploy_infrastructure
    fi
    
    configure_kubectl
    install_jupyterhub
    get_jupyterhub_url
    
    print_status "Deployment complete!"
    print_status ""
    print_status "Next steps:"
    print_status "1. Configure GitHub OAuth in helm/jupyterhub-values.yaml"
    print_status "2. Set up DNS for your JupyterHub instance"
    print_status "3. Enable HTTPS with cert-manager"
    print_status "4. Configure monitoring with Prometheus/Grafana"
    print_status ""
    print_status "To access JupyterHub admin panel: http://$JUPYTERHUB_URL/hub/admin"
}

# Run main function
main "$@"