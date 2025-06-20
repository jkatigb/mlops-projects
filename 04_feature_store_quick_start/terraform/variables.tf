variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "s3_bucket_name" {
  description = "Name of S3 bucket for offline store"
  type        = string
  
  validation {
    condition     = can(regex("^[a-z0-9][a-z0-9.-]*[a-z0-9]$", var.s3_bucket_name)) && length(var.s3_bucket_name) >= 3 && length(var.s3_bucket_name) <= 63
    error_message = "S3 bucket name must be 3-63 characters, start and end with lowercase letter or number, and contain only lowercase letters, numbers, periods, and hyphens."
  }
}

variable "dynamodb_table_name" {
  description = "Name of DynamoDB table for online store"
  type        = string
  
  validation {
    condition     = can(regex("^[a-zA-Z0-9_.-]+$", var.dynamodb_table_name)) && length(var.dynamodb_table_name) >= 3 && length(var.dynamodb_table_name) <= 255
    error_message = "DynamoDB table name must be 3-255 characters and contain only letters, numbers, underscores, periods, and hyphens."
  }
}

variable "enable_force_destroy" {
  description = "Allow destruction of S3 bucket with objects (use with caution)"
  type        = bool
  default     = false
}
