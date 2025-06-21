output "cluster_name" {
  description = "Name of the EKS cluster"
  value       = module.eks.cluster_name
}

output "cluster_endpoint" {
  description = "Endpoint for EKS control plane"
  value       = module.eks.cluster_endpoint
}

output "cluster_security_group_id" {
  description = "Security group ID for the cluster"
  value       = module.eks.cluster_security_group_id
}

output "jupyterhub_role_arn" {
  description = "IAM role ARN for JupyterHub service account"
  value       = module.jhub_sa.role_arn
}

output "jupyterhub_namespace" {
  description = "Kubernetes namespace for JupyterHub"
  value       = var.jupyterhub_namespace
}

output "kubeconfig_command" {
  description = "Command to update kubeconfig"
  value       = "aws eks update-kubeconfig --region ${var.region} --name ${module.eks.cluster_name}"
}

output "jupyterhub_url" {
  description = "Command to get JupyterHub URL after installation"
  value       = "kubectl get svc -n ${var.jupyterhub_namespace} proxy-public -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'"
}

output "vpc_id" {
  description = "ID of the VPC"
  value       = module.vpc.vpc_id
}

output "s3_bucket_name" {
  description = "S3 bucket for JupyterHub user storage"
  value       = aws_s3_bucket.jupyterhub_storage.id
}