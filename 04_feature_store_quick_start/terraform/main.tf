terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
  }
}

provider "aws" {
  region = var.region
}

resource "aws_s3_bucket" "offline_store" {
  bucket        = var.s3_bucket_name
  force_destroy = var.enable_force_destroy
}

resource "aws_s3_bucket_lifecycle_configuration" "offline_store" {
  bucket = aws_s3_bucket.offline_store.id

  rule {
    id     = "delete-old-features"
    status = "Enabled"

    expiration {
      days = 90
    }
  }
}

resource "aws_dynamodb_table" "online_store" {
  name         = var.dynamodb_table_name
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "feature_id"

  attribute {
    name = "feature_id"
    type = "S"
  }
  
  point_in_time_recovery {
    enabled = true
  }
}
