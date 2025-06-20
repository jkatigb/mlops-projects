variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "s3_bucket_name" {
  description = "Name of S3 bucket for offline store"
  type        = string
}

variable "dynamodb_table_name" {
  description = "Name of DynamoDB table for online store"
  type        = string
}
