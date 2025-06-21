variable "region" {
  type        = string
  default     = "us-west-2"
  description = "AWS region for deployment"
}

variable "cluster_name" {
  type        = string
  default     = "jhub"
  description = "EKS cluster name"
}

variable "environment" {
  type        = string
  default     = "dev"
  description = "Environment name"
}

variable "vpc_cidr" {
  type        = string
  default     = "10.0.0.0/16"
  description = "CIDR block for VPC"
}

variable "availability_zones" {
  type        = list(string)
  default     = ["us-west-2a", "us-west-2b", "us-west-2c"]
  description = "List of availability zones"
}

variable "kubernetes_version" {
  type        = string
  default     = "1.29"
  description = "Kubernetes version for EKS cluster"
}

variable "enable_gpu_nodes" {
  type        = bool
  default     = true
  description = "Enable GPU node group for JupyterHub"
}

variable "jupyterhub_namespace" {
  type        = string
  default     = "jhub"
  description = "Kubernetes namespace for JupyterHub"
}

variable "jupyterhub_s3_bucket" {
  type        = string
  default     = ""
  description = "S3 bucket for JupyterHub user storage (leave empty to create new)"
}

variable "tags" {
  type        = map(string)
  default     = {}
  description = "Tags to apply to all resources"
}