# Self-Service JupyterHub on AWS EKS

A production-ready deployment of JupyterHub on AWS EKS with GPU support, auto-scaling, and secure multi-user environments for data science teams.

## Features

- **Multi-User Support**: GitHub OAuth authentication with organization-based access control
- **GPU Support**: NVIDIA T4 GPU nodes for deep learning workloads
- **Auto-Scaling**: Cluster autoscaling based on resource demand
- **Persistent Storage**: User data persistence with S3 integration
- **Multiple Profiles**: Pre-configured compute profiles (CPU/GPU, various sizes)
- **Security**: IAM roles for service accounts (IRSA), network policies, and secure defaults
- **Cost Optimization**: Automatic culling of idle instances, spot instance support

## Architecture

```
┌─────────────────┐     ┌──────────────────┐
│   Users         │────▶│  Load Balancer   │
└─────────────────┘     └──────────────────┘
                               │
                        ┌──────▼──────┐
                        │ JupyterHub  │
                        │    Proxy    │
                        └──────┬──────┘
                               │
                ┌──────────────┴──────────────┐
                │                             │
          ┌─────▼─────┐                ┌─────▼─────┐
          │    Hub    │                │   User    │
          │  Service  │                │   Pods    │
          └─────┬─────┘                └─────┬─────┘
                │                             │
                └──────────┬──────────────────┘
                           │
                    ┌──────▼──────┐
                    │     EKS     │
                    │   Cluster   │
                    └──────┬──────┘
                           │
         ┌─────────────────┼─────────────────┐
         │                 │                 │
    ┌────▼────┐      ┌────▼────┐      ┌────▼────┐
    │  System │      │   CPU   │      │   GPU   │
    │  Nodes  │      │  Nodes  │      │  Nodes  │
    └─────────┘      └─────────┘      └─────────┘
```

## Tech Stack

- **Infrastructure**: AWS EKS, VPC, IAM, S3, KMS
- **Orchestration**: Kubernetes 1.29, Helm 3.x
- **Compute**: EC2 (T3 for CPU, G4dn for GPU), Spot instances
- **Networking**: AWS Load Balancer Controller, VPC CNI
- **Storage**: EBS CSI Driver, S3 FUSE
- **Security**: IRSA, Network Policies, Pod Security Standards
- **Monitoring**: CloudWatch Logs, optional Prometheus/Grafana

## Quick Start

### Prerequisites

- AWS CLI configured with appropriate credentials
- Terraform >= 1.0
- kubectl >= 1.24
- Helm >= 3.0
- GitHub OAuth App (for authentication)

### Deploy Infrastructure

```bash
# Clone the repository
cd 07_self_service_jupyterhub_eks

# Configure variables
cp terraform/terraform.tfvars.example terraform/terraform.tfvars
# Edit terraform/terraform.tfvars with your settings

# Deploy AWS infrastructure
cd terraform
terraform init
terraform plan
terraform apply

# Configure kubectl
aws eks update-kubeconfig --region $(terraform output -raw region) --name $(terraform output -raw cluster_name)
```

### Install JupyterHub

```bash
# Add JupyterHub Helm repository
helm repo add jupyterhub https://jupyterhub.github.io/helm-chart/
helm repo update

# Update Helm values with your configuration
# Edit helm/jupyterhub-values.yaml with GitHub OAuth credentials

# Install JupyterHub
helm upgrade --install jupyterhub jupyterhub/jupyterhub \
  --namespace jupyterhub \
  --values helm/jupyterhub-values.yaml \
  --version 3.3.7

# Get JupyterHub URL
kubectl get svc -n jupyterhub proxy-public -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'
```

## User Profiles

| Profile | CPU | Memory | GPU | Use Case |
|---------|-----|--------|-----|----------|
| Minimal | 0.5-2 | 1-4 GB | - | Light development |
| Standard | 2-4 | 4-8 GB | - | Regular data science |
| Large | 4-8 | 16-32 GB | - | Memory-intensive work |
| GPU | 4-8 | 16-32 GB | 1x T4 | Deep learning |

## Cost Optimization

- **Spot Instances**: 60-90% savings on compute
- **Auto-scaling**: Nodes scale based on demand
- **Idle Culling**: Automatic shutdown after 1 hour
- **Right-sizing**: Multiple profiles for different workloads

## Security Features

- **Authentication**: GitHub OAuth with org restrictions
- **Authorization**: Admin users and RBAC
- **Network**: Private subnets, security groups, network policies
- **Data**: Encrypted at rest (S3, EBS), user isolation
- **Secrets**: AWS Secrets Manager, Kubernetes secrets

## Maintenance

See the full README for detailed instructions on:
- Upgrading JupyterHub
- Scaling node groups
- Backup and recovery
- Monitoring and troubleshooting
- Advanced configuration

## Clean Up

```bash
# Delete JupyterHub
helm uninstall jupyterhub -n jupyterhub

# Destroy infrastructure
cd terraform
terraform destroy
```

---
*Status*: Production-ready

