variable "namespace" {
  type        = string
  description = "Kubernetes namespace for the service account"
}

variable "service_account_name" {
  type        = string
  description = "Name of the Kubernetes service account"
}

variable "cluster_oidc_provider_arn" {
  type        = string
  description = "ARN of the EKS cluster's OIDC provider"
}

variable "policies" {
  type        = list(string)
  default     = []
  description = "List of IAM policy ARNs to attach to the role"
}

variable "tags" {
  type        = map(string)
  default     = {}
  description = "Tags to apply to IAM resources"
}

provider "aws" {}

data "aws_iam_openid_connect_provider" "this" {
  arn = var.cluster_oidc_provider_arn
}

data "aws_iam_policy_document" "assume" {
  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]
    principals {
      type        = "Federated"
      identifiers = [var.cluster_oidc_provider_arn]
    }
    condition {
      test     = "StringEquals"
      variable = "${replace(data.aws_iam_openid_connect_provider.this.url, \"https://\", \"")}:sub"
      values   = ["system:serviceaccount:${var.namespace}:${var.service_account_name}"]
    }
  }
}

resource "aws_iam_role" "this" {
  name               = "irsa-${var.service_account_name}"
  assume_role_policy = data.aws_iam_policy_document.assume.json
  tags               = var.tags
}

resource "aws_iam_role_policy_attachment" "custom" {
  count      = length(var.policies)
  role       = aws_iam_role.this.name
  policy_arn = var.policies[count.index]
}

output "role_arn" { value = aws_iam_role.this.arn }
