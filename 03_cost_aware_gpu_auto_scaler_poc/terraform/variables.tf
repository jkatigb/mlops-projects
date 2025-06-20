variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
  
  validation {
    condition     = contains(["us-east-1", "us-west-2", "eu-west-1", "eu-central-1", "ap-southeast-1"], var.region)
    error_message = "Region must be one of: us-east-1, us-west-2, eu-west-1, eu-central-1, ap-southeast-1."
  }
}

variable "name" {
  description = "Base name for resources"
  type        = string
  default     = "gpu-poc"
}
