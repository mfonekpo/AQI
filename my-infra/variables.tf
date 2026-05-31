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