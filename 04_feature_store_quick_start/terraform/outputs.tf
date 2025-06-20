output "s3_bucket" {
  value = aws_s3_bucket.offline_store.id
}

output "dynamodb_table" {
  value = aws_dynamodb_table.online_store.id
}
