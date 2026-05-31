# terraform.tfvars

aws_region  = "us-east-1"        # The AWS region to deploy resources in
environment = "dev"              # The environment to deploy resources in (e.g., dev, staging, prod)
queue_name  = "aqi-sensor-queue" # Name of the SQS queue to be created
transform_queue_name = "aqi-transform-queue" # Name of the SQS queue for transformation


# Bucket definitions for S3
s3_buckets = {
  staging = {
    name        = "aqi-staging"
    environment = "dev"
  }
  transform = {
    name        = "aqi-transform"
    environment = "dev"
  }
}
