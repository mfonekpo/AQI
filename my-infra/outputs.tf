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