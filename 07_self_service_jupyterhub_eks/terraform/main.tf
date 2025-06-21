locals {
  common_tags = merge(
    var.tags,
    {
      Environment = var.environment
      Project     = "jupyterhub"
      ManagedBy   = "terraform"
    }
  )
}

# VPC Module
module "vpc" {
  source = "./modules/vpc"

  vpc_cidr           = var.vpc_cidr
  cluster_name       = var.cluster_name
  availability_zones = var.availability_zones
  enable_nat_gateway = true
  single_nat_gateway = var.environment == "dev" ? true : false
  tags               = local.common_tags
}

# EKS Module
module "eks" {
  source = "./modules/eks"

  cluster_name       = var.cluster_name
  kubernetes_version = var.kubernetes_version
  vpc_id             = module.vpc.vpc_id
  public_subnet_ids  = module.vpc.public_subnet_ids
  private_subnet_ids = module.vpc.private_subnet_ids
  enable_gpu_nodes   = var.enable_gpu_nodes
  tags               = local.common_tags
}

# Create namespace for JupyterHub
resource "kubernetes_namespace" "jupyterhub" {
  metadata {
    name = var.jupyterhub_namespace
    labels = {
      name = var.jupyterhub_namespace
    }
  }

  depends_on = [module.eks]
}

# S3 bucket for JupyterHub user storage
resource "aws_s3_bucket" "jupyterhub_storage" {
  bucket = var.jupyterhub_s3_bucket != "" ? var.jupyterhub_s3_bucket : "${var.cluster_name}-jupyterhub-storage-${data.aws_caller_identity.current.account_id}"

  tags = merge(
    local.common_tags,
    {
      Name = "${var.cluster_name}-jupyterhub-storage"
    }
  )
}

# Enable versioning for user data protection
resource "aws_s3_bucket_versioning" "jupyterhub_storage" {
  bucket = aws_s3_bucket.jupyterhub_storage.id
  versioning_configuration {
    status = "Enabled"
  }
}

# Enable encryption at rest
resource "aws_s3_bucket_server_side_encryption_configuration" "jupyterhub_storage" {
  bucket = aws_s3_bucket.jupyterhub_storage.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Block public access to the bucket
resource "aws_s3_bucket_public_access_block" "jupyterhub_storage" {
  bucket = aws_s3_bucket.jupyterhub_storage.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# IAM policy for JupyterHub to access S3
resource "aws_iam_policy" "jupyterhub_s3_access" {
  name        = "${var.cluster_name}-jupyterhub-s3-access"
  description = "Policy for JupyterHub to access S3 bucket"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:ListBucket"
        ]
        Resource = aws_s3_bucket.jupyterhub_storage.arn
        Condition = {
          StringLike = {
            "s3:prefix" = ["home/$${aws:username}/*"]
          }
        }
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject"
        ]
        Resource = "${aws_s3_bucket.jupyterhub_storage.arn}/home/$${aws:username}/*"
      }
    ]
  })
}

# IRSA for JupyterHub service account
module "jhub_sa" {
  source = "./modules/iam-irsa"

  namespace                 = kubernetes_namespace.jupyterhub.metadata[0].name
  service_account_name      = "hub"
  cluster_oidc_provider_arn = module.eks.oidc_provider_arn
  policies                  = [aws_iam_policy.jupyterhub_s3_access.arn]
  tags                      = local.common_tags
}

# Generate a secure token for JupyterHub
resource "random_password" "jupyterhub_secret_token" {
  length  = 64
  special = false
}

# Store the token in AWS Secrets Manager
resource "aws_secretsmanager_secret" "jupyterhub_token" {
  name_prefix = "${var.cluster_name}-jupyterhub-token-"
  description = "Secret token for JupyterHub"

  tags = local.common_tags
}

resource "aws_secretsmanager_secret_version" "jupyterhub_token" {
  secret_id = aws_secretsmanager_secret.jupyterhub_token.id
  secret_string = jsonencode({
    token = random_password.jupyterhub_secret_token.result
  })
}

# Create a Kubernetes secret for JupyterHub
resource "kubernetes_secret" "jupyterhub" {
  metadata {
    name      = "jupyterhub-secret"
    namespace = kubernetes_namespace.jupyterhub.metadata[0].name
  }

  data = {
    hub.config.JupyterHub.cookie_secret = base64encode(random_password.jupyterhub_secret_token.result)
    hub.config.CryptKeeper.keys         = base64encode(random_password.jupyterhub_secret_token.result)
  }

  depends_on = [kubernetes_namespace.jupyterhub]
}

# Data sources
data "aws_caller_identity" "current" {}

# Configure Kubernetes provider
provider "kubernetes" {
  host                   = module.eks.cluster_endpoint
  cluster_ca_certificate = base64decode(module.eks.cluster_certificate_authority_data)

  exec {
    api_version = "client.authentication.k8s.io/v1beta1"
    command     = "aws"
    args = [
      "eks",
      "get-token",
      "--cluster-name",
      module.eks.cluster_name
    ]
  }
}