output "bucket_ids" {
  description = "Names of all S3 buckets"
  value       = { for key, bucket in aws_s3_bucket.buckets : key => bucket.id }
}

output "bucket_arns" {
  description = "ARNs of all S3 buckets"
  value = {
    for key, bucket in aws_s3_bucket.buckets :
    key => bucket.arn
  }
}

output "terraform_role_arn" {
  value       = aws_iam_role.terraform_role.arn
  description = "ARN of the Terraform provisioner role"
}

output "data_pipeline_role_arn" {
  value       = aws_iam_role.data_pipeline_role.arn
  description = "ARN of the data pipeline role"
}