variable "aws_region" {
  type        = string
  description = "AWS region to deploy resources in"
  default     = "us-east-1"
}

variable "name" {
  type        = string
  description = "Resource name prefix (e.g., project or environment identifier)"
  default     = "demo"
}
variable "vpc_cidr" { default = "10.0.0.0/16" }
variable "public_subnets" {
  type        = list(string)
  description = "List of public subnet CIDR blocks for the VPC"
  default     = ["10.0.1.0/24", "10.0.2.0/24"]

  validation {
    condition     = length(var.public_subnets) == length(var.azs)
    error_message = "The number of public_subnets must match the number of availability zones."
  }
}

variable "azs" {
  type        = list(string)
  description = "List of availability zones for resource placement"
  default     = ["us-east-1a", "us-east-1b"]

  validation {
    condition     = length(var.azs) > 0
    error_message = "At least one availability zone must be specified."
  }
}
