terraform {
  required_providers {
    aws = {
        source = "hashicorp/aws"
        version = "~> 6.0"
    }
  }
}

# configure the AWS Provider
provider "aws" {
    region = var.aws_region
    profile = "terraform"

# This tells terraform to assume the IAM role
# Instead of using using static credentials

# assume_role {
#     role_arn = var.terraform_role_arn
#     duration = "12h" # 12 hours
# }

}
