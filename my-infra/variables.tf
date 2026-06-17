variable "aws_region" {
  description = "The AWS region to deploy resources in."
  type        = string
  default     = "us-east-1"
}

variable "s3_buckets" {
  description = "Map of S3 buckets to create"
  type = map(object({
    name        = string
    environment = string
  }))
}

variable "environment" {
  description = "The environment to deploy resources in."
  type        = string
  default     = "dev"
}

variable "queue_name" {
  description = "The name of the SQS queue."
  type        = string
}

variable "transform_queue_name" {
  description = "SQS Queue for transformation"
  type        = string
}

# Snowflake variables
variable "snowflake_organization_name" {
  description = "Snowflake organization name"
  type        = string
  sensitive   = true
  ephemeral   = true
}

variable "snowflake_account_name" {
  description = "Snowflake account name"
  type        = string
  sensitive   = true
  ephemeral   = true
}

variable "snowflake_user" {
  description = "Snowflake user name"
  type        = string
  sensitive   = true
  ephemeral   = true
}

variable "snowflake_role" {
  description = "Snowflake role name"
  type        = string
  sensitive   = true
  ephemeral   = true
}


variable "schema_name" {
  description = "Snowflake schema name"
  type        = string
}

variable "db_name" {
  description = "Snowflake database name"
  type        = string
}


variable "s3_storage_name" {
  description = "Snowflake external storage name for integration"
  type        = string
}

variable "snowflake_iam_user_arn" {
  description = "Snowflake IAM user ARN"
  type        = string
  sensitive   = true
}

variable "snowflake_external_id" {
  description = "Snowflake external ID"
  type        = string
  sensitive   = true
}


variable "table_name" {
  description = "Snowflake table name"
  type        = string
  sensitive   = true
}

variable "warehouse_name" {
  description = "Snowflake warehouse name"
  type        = string
  sensitive   = true
}