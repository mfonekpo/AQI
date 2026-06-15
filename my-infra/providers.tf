terraform {
  required_providers {
    # AWS
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
    # Snowflake
    snowflake = {
      source = "snowflakedb/snowflake"
    }
  }
}

# configure the AWS Provider
provider "aws" {
  region  = var.aws_region
  profile = "terraform"
}

locals {
  private_key_path = pathexpand("~/.ssh/snowflake_tf_snow_key.p8")
}

# configure snowflake provider with private key authentication
provider "snowflake" {
  organization_name = var.snowflake_organization_name
  account_name      = var.snowflake_account_name
  user              = var.snowflake_user
  role              = var.snowflake_role
  authenticator     = "SNOWFLAKE_JWT"
  private_key       = file(local.private_key_path)
  preview_features_enabled = [
    "snowflake_storage_integration_aws_resource",
    "snowflake_file_format_resource",
    "snowflake_stage_external_s3_resource"
  ]
}