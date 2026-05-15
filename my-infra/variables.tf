variable "aws_region" {
  description = "The AWS region to deploy resources in."
  type        = string
  default     = "us-east-1"
}

# variable "terraform_role_arn" {
#   description = "The ARN of the IAM role to assume."
#   type        = string
# }

variable "s3_buckets" {
    description = "Map of S3 buckets to create"
    type        = map(object({
        name = string
        environment = string
    }))
}

variable "environment" {
    description = "The environment to deploy resources in."
    type        = string
    default     = "dev"
}

variable "data_pipeline_role_arn" {
  description = "ARN of the role that will access the bucket"
  type        = string
}