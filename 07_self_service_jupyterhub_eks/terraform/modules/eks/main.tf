variable "cluster_name" {
  type        = string
  default     = "jhub"
  description = "EKS cluster name"
}

variable "kubernetes_version" {
  type        = string
  default     = "1.29"
  description = "Kubernetes version for EKS cluster"
}

variable "vpc_id" {
  type        = string
  description = "VPC ID where EKS cluster will be deployed"
}

variable "public_subnet_ids" {
  type        = list(string)
  description = "List of public subnet IDs"
}

variable "private_subnet_ids" {
  type        = list(string)
  description = "List of private subnet IDs"
}

variable "enable_gpu_nodes" {
  type        = bool
  default     = true
  description = "Enable GPU node group"
}

variable "tags" {
  type        = map(string)
  default     = {}
  description = "Tags to apply to all resources"
}

module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 20.0"

  cluster_name                   = var.cluster_name
  cluster_version                = var.kubernetes_version
  cluster_endpoint_public_access = true

  vpc_id     = var.vpc_id
  subnet_ids = concat(var.public_subnet_ids, var.private_subnet_ids)

  # Enable IRSA
  enable_irsa = true

  # Enable cluster encryption
  cluster_encryption_config = {
    provider_key_arn = aws_kms_key.eks.arn
    resources        = ["secrets"]
  }

  # Enable control plane logging
  cluster_enabled_log_types = ["api", "audit", "authenticator", "controllerManager", "scheduler"]

  # EKS Addons
  cluster_addons = {
    coredns = {
      most_recent = true
    }
    kube-proxy = {
      most_recent = true
    }
    vpc-cni = {
      most_recent = true
    }
    aws-ebs-csi-driver = {
      most_recent = true
    }
  }

  # Node groups
  eks_managed_node_groups = {
    # CPU node group for system workloads
    system = {
      name = "${var.cluster_name}-system"

      instance_types = ["t3.medium"]
      capacity_type  = "ON_DEMAND"

      min_size     = 2
      max_size     = 4
      desired_size = 2

      subnet_ids = var.private_subnet_ids

      # Labels and taints for system workloads
      labels = {
        role = "system"
      }

      taints = []

      tags = merge(
        var.tags,
        {
          Name = "${var.cluster_name}-system"
        }
      )
    }

    # CPU node group for user workloads
    cpu = {
      name = "${var.cluster_name}-cpu"

      instance_types = ["t3.xlarge", "t3a.xlarge"]
      capacity_type  = "SPOT"

      min_size     = 1
      max_size     = 10
      desired_size = 2

      subnet_ids = var.private_subnet_ids

      labels = {
        role     = "user"
        workload = "cpu"
      }

      taints = []

      # User data for additional setup
      pre_bootstrap_user_data = <<-EOT
        #!/bin/bash
        # Install SSM agent for debugging
        yum install -y amazon-ssm-agent
        systemctl enable amazon-ssm-agent
        systemctl start amazon-ssm-agent
      EOT

      tags = merge(
        var.tags,
        {
          Name = "${var.cluster_name}-cpu"
        }
      )
    }
  }

  # Conditionally create GPU node group
  eks_managed_node_group_defaults = {
    iam_role_additional_policies = {
      AmazonSSMManagedInstanceCore = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
    }
  }

  tags = var.tags
}

# GPU node group (created separately to handle conditional creation)
resource "aws_eks_node_group" "gpu" {
  count = var.enable_gpu_nodes ? 1 : 0

  cluster_name    = module.eks.cluster_name
  node_group_name = "${var.cluster_name}-gpu"
  node_role_arn   = module.eks.eks_managed_node_groups["system"].iam_role_arn
  subnet_ids      = var.private_subnet_ids

  scaling_config {
    desired_size = 0
    max_size     = 5
    min_size     = 0
  }

  instance_types = ["g4dn.xlarge", "g4dn.2xlarge"]
  capacity_type  = "SPOT"

  labels = {
    role                  = "user"
    workload              = "gpu"
    "nvidia.com/gpu"      = "true"
    "k8s.amazonaws.com/accelerator" = "nvidia-tesla-t4"
  }

  # Taint GPU nodes so only GPU workloads are scheduled
  taint {
    key    = "nvidia.com/gpu"
    value  = "true"
    effect = "NO_SCHEDULE"
  }

  # Install GPU drivers
  ami_type = "AL2_x86_64_GPU"

  tags = merge(
    var.tags,
    {
      Name = "${var.cluster_name}-gpu"
    }
  )

  lifecycle {
    ignore_changes = [scaling_config[0].desired_size]
  }

  depends_on = [
    module.eks
  ]
}

# KMS key for cluster encryption
resource "aws_kms_key" "eks" {
  description             = "EKS cluster encryption key"
  deletion_window_in_days = 10
  enable_key_rotation     = true

  tags = merge(
    var.tags,
    {
      Name = "${var.cluster_name}-eks-kms"
    }
  )
}

resource "aws_kms_alias" "eks" {
  name          = "alias/${var.cluster_name}-eks"
  target_key_id = aws_kms_key.eks.key_id
}

# NVIDIA device plugin for GPU support
resource "kubernetes_daemonset" "nvidia_device_plugin" {
  count = var.enable_gpu_nodes ? 1 : 0

  metadata {
    name      = "nvidia-device-plugin-daemonset"
    namespace = "kube-system"
  }

  spec {
    selector {
      match_labels = {
        name = "nvidia-device-plugin-ds"
      }
    }

    template {
      metadata {
        labels = {
          name = "nvidia-device-plugin-ds"
        }
      }

      spec {
        toleration {
          key      = "nvidia.com/gpu"
          operator = "Exists"
          effect   = "NoSchedule"
        }

        priority_class_name = "system-node-critical"

        container {
          name  = "nvidia-device-plugin-ctr"
          image = "nvcr.io/nvidia/k8s-device-plugin:v0.14.5"

          security_context {
            allow_privilege_escalation = false
            capabilities {
              drop = ["ALL"]
            }
          }

          volume_mount {
            name       = "device-plugin"
            mount_path = "/var/lib/kubelet/device-plugins"
          }
        }

        volume {
          name = "device-plugin"
          host_path {
            path = "/var/lib/kubelet/device-plugins"
          }
        }

        node_selector = {
          "nvidia.com/gpu" = "true"
        }
      }
    }
  }

  depends_on = [
    module.eks,
    aws_eks_node_group.gpu
  ]
}

# Outputs
output "cluster_id" {
  description = "EKS cluster ID"
  value       = module.eks.cluster_id
}

output "cluster_name" {
  description = "EKS cluster name"
  value       = module.eks.cluster_name
}

output "cluster_endpoint" {
  description = "Endpoint for EKS control plane"
  value       = module.eks.cluster_endpoint
}

output "cluster_security_group_id" {
  description = "Security group ids attached to the cluster control plane"
  value       = module.eks.cluster_security_group_id
}

output "oidc_provider_arn" {
  description = "ARN of the OIDC Provider for EKS"
  value       = module.eks.oidc_provider_arn
}

output "cluster_certificate_authority_data" {
  description = "Base64 encoded certificate data required to communicate with the cluster"
  value       = module.eks.cluster_certificate_authority_data
  sensitive   = true
}