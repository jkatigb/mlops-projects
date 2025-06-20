resource "aws_cloudwatch_log_group" "eks" {
  name = "/aws/eks/${module.eks.cluster_name}/cluster"
  retention_in_days = 7
}

resource "aws_cloudwatch_metric_filter" "gpu_cost" {
  name           = "gpuCostByNamespace"
  log_group_name = aws_cloudwatch_log_group.eks.name
  pattern        = "namespace=* cost=*"

  metric_transformation {
    name      = "namespaceCost"
    namespace = "GPUCost"
    value     = "$cost"
    default_value = 0
  }
}
