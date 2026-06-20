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

# output "snowflake_iam_user_arn" {
#   value = snowflake_storage_integration_aws.tf_s3_integration.storage_aws_iam_user_arn
# }

# output "snowflake_external_id" {
#   value = snowflake_storage_integration_aws.tf_s3_integration.storage_aws_external_id
# }