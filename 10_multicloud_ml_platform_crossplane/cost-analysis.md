# Cost Analysis Notes

*As of June 2025*

## AWS Costs
* EKS control plane: ~$73/month per cluster ([AWS EKS Pricing](https://aws.amazon.com/eks/pricing/))
* Worker nodes: Variable based on EC2 instance types
* Inter-region data transfer: $0.02/GB ([AWS Data Transfer Pricing](https://aws.amazon.com/ec2/pricing/on-demand/#Data_Transfer))

## GCP Costs
* GKE Autopilot: ~$0.10/vCPU-hour for minimal cluster ([GKE Pricing](https://cloud.google.com/kubernetes-engine/pricing))
* Assumes 2 vCPUs minimum for system workloads
* Inter-region egress: $0.05/GB ([GCP Network Pricing](https://cloud.google.com/vpc/network-pricing))

## Crossplane Overhead
* Crossplane itself adds no cost beyond the Kubernetes resources it manages
* Runs as pods in the management cluster (minimal resource usage)

## Assumptions
* Costs based on us-east-1 (AWS) and us-central1 (GCP) regions
* Minimal cluster configuration (2-3 nodes)
* Does not include storage, load balancer, or additional services

