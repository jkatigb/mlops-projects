# Example Terraform configuration for testing evidence collection
terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# Example S3 bucket for ML artifacts
resource "aws_s3_bucket" "ml_artifacts" {
  bucket_prefix = "ml-artifacts-"
  
  tags = {
    Environment = "dev"
    Purpose     = "ML Pipeline Artifacts"
    Compliance  = "SOC2"
  }
}

# Enable versioning for audit trail
resource "aws_s3_bucket_versioning" "ml_artifacts" {
  bucket = aws_s3_bucket.ml_artifacts.id
  versioning_configuration {
    status = "Enabled"
  }
}

# Output bucket name for evidence collection
output "artifacts_bucket" {
  value = aws_s3_bucket.ml_artifacts.id
  description = "S3 bucket for ML artifacts"
}