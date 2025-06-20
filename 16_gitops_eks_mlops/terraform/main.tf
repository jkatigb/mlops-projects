module "vpc" {
  source         = "./modules/vpc"
  name           = var.name
  cidr_block     = var.cidr_block
  public_subnets = var.public_subnets
  azs            = var.azs
}
}

module "eks" {
  source       = "./modules/eks"
  cluster_name = "${var.name}-cluster"
  vpc_id       = module.vpc.vpc_id
  subnet_ids   = module.vpc.subnet_ids
}

resource "aws_ecr_repository" "mlops" {
  name = "${var.name}-mlops"

  image_scanning_configuration {
    scan_on_push = true
  }
}

output "cluster_endpoint" {
  value = module.eks.cluster_endpoint
}
