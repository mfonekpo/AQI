# terraform.tfvars
aws_region = "us-east-1"
# terraform_role_arn = "arn:aws:iam::158449849022:role/terraform-provisioner-role"
environment = "dev"
data_pipeline_role_arn = "arn:aws:iam::158449849022:role/data-pipeline-role"
s3_buckets = {
  staging = {
    name        = "aqi.staging"
    environment = "dev"
  }
  transform = {
    name        = "aqi.transform"
    environment = "dev"
  }
}