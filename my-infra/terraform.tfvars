# terraform.tfvars
aws_region = "us-east-1"
environment = "dev"

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