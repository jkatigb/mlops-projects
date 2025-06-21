# Per-user S3 Access via IRSA

Each JupyterHub user receives a dedicated IAM role bound to a Kubernetes ServiceAccount. When a notebook spawns, KubeSpawner sets the role ARN using the `iam.amazonaws.com/role` annotation. This role grants access only to the user's S3 prefix.

```yaml
singleuser:
  awsRole: arn:aws:iam::123456789012:role/jhub-user-{username}
  extraAnnotations:
    iam.amazonaws.com/role: "arn:aws:iam::123456789012:role/jhub-user-{username}"
```

Create IAM policies with a bucket policy like:

```hcl
resource "aws_iam_policy" "user_s3" {
  name   = "jhub-user-${var.username}-s3"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["s3:*"]
      Resource = [
        "arn:aws:s3:::mybucket/${var.username}/*"
      ]
    }]
  })
}
```

Attach the policy using the `iam-irsa` module.
