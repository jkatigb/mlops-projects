module "vpc" {
  source = "./modules/vpc"
  region = var.region
}

module "eks" {
  source            = "./modules/eks"
  region            = var.region
  vpc_id            = module.vpc.vpc_id
  public_subnet_ids = module.vpc.public_subnet_ids
}

module "jhub_sa" {
  source                   = "./modules/iam-irsa"
  namespace                = "jhub"
  service_account_name     = "hub"
  cluster_oidc_provider_arn = module.eks.oidc_provider_arn
  policies                 = ["arn:aws:iam::aws:policy/AmazonS3FullAccess"]
}

output "cluster_name" { value = module.eks.cluster_name }
output "jhub_role_arn" { value = module.jhub_sa.role_arn }
