output "cluster_name" {
  description = "Name of the provisioned EKS cluster"
  value       = module.eks.cluster_name
}

output "cluster_endpoint" {
  description = "API endpoint of the provisioned EKS cluster"
  value       = module.eks.cluster_endpoint
}
