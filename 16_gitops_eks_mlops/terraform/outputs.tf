output "cluster_endpoint" { value = module.eks.cluster_endpoint }
output "ecr_repository" { value = aws_ecr_repository.mlops.repository_url }
