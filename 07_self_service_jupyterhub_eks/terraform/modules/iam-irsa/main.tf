variable "namespace" {}
variable "service_account_name" {}
variable "cluster_oidc_provider_arn" {}
variable "policies" { type = list(string) default = [] }

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
}

resource "aws_iam_role_policy_attachment" "custom" {
  count      = length(var.policies)
  role       = aws_iam_role.this.name
  policy_arn = var.policies[count.index]
}

output "role_arn" { value = aws_iam_role.this.arn }
