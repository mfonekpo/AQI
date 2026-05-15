#1. THE ROLE - the identity terraform assumes

resource "aws_iam_role" "terraform_role" {
  name = "terraform-provisioner-role"
  description = "Role assumed by Terraform to provision infra"

# Trust Policy - Who can assume this role
assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
        {
            Action = "sts:AssumeRole"
            Effect = "Allow"
            Principal = {
                AWS = "arn:aws:iam::158449849022:user/aqi_user"
            }
        }
    ]
})

tags = {
    Environment = var.environment
    Managedby = "Terraform"
    }
}


# 2. THE POLICY — WHAT the role is allowed to do

resource "aws_iam_policy" "terraform_s3_policy" {
  name = "terraform-s3-provisioning-policy"
  description = "Least privilege policy for Terraform to provision S3 resources"

  policy = jsonencode({
    version = "2012-10-17"
    statement = [
        {
            Action = [
                # Bucket level
                "s3:CreateBucket",
                "s3:DeleteBucket",
                "s3:ListBucket",
                "s3:GetBucketLocation",

                # Bucket policy & config
                "s3:GetBucketPolicy",
                "s3:PutBucketPolicy",
                "s3:DeleteBucketPolicy",
                "s3:PutBucketVersioning",
                "s3:GetBucketVersioning",
                "s3:PutEncryptionConfiguration",
                "s3:GetEncryptionConfiguration",
                "s3:PutBucketPublicAccessBlock",
                "s3:GetBucketPublicAccessBlock"
            ]
            Effect = "Allow"
            Resource = "*"
            Sid = "S3BucketManagement"
        }
    ]
  })

}


# 3. ATTACH THE POLICY TO THE ROLE

resource "aws_iam_role_policy_attachment" "terraform_s3_attach" {
  role       = aws_iam_role.terraform_role.name
  policy_arn = aws_iam_policy.terraform_s3_policy.arn
}


# 4. SEPARATE ROLE for your data pipeline
resource "aws_iam_role" "data_pipeline_role" {
  name        = "data-pipeline-role"
  description = "Role assumed by the data pipeline to read/write S3"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect    = "Allow"
        Principal = {
          AWS = "arn:aws:iam::158449849022:user/aqi_user"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_policy" "data_pipeline_s3_policy" {
  name        = "data-pipeline-s3-access-policy"
  description = "Allows data pipeline to read/write specific S3 bucket"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "BucketAccess"
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = flatten([
            for bucket in aws_s3_bucket.buckets :
            [
                bucket.arn,                # Bucket ARN for ListBucket
                "${bucket.arn}/*"         # Object ARNs for Get/Put/Delete
            ]
        ])
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "data_pipeline_s3_attach" {
  role       = aws_iam_role.data_pipeline_role.name
  policy_arn = aws_iam_policy.data_pipeline_s3_policy.arn
}