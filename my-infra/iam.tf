resource "aws_iam_role" "snowflake_storage_role" {
  name = "snowflake-storage-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          AWS = "*"
          # AWS = snowflake_storage_integration_aws.tf_s3_integration.storage_aws_iam_user_arn
        }
        # Condition = {
        #   StringEquals = {
        #     "sts:ExternalId" = snowflake_storage_integration_aws.tf_s3_integration.storage_aws_external_id
        #   }
        # }
      }
    ]
  })
}


resource "aws_iam_role_policy" "snowflake_s3_access" {

  name = "snowflake-s3-access"
  role = aws_iam_role.snowflake_storage_role.id

  policy = jsonencode({
    Version = "2012-10-17"

    Statement = [

      {
        Sid    = "ListBucket"
        Effect = "Allow"

        Action = [
          "s3:ListBucket"
        ]

        Resource = [
          aws_s3_bucket.buckets["transform"].arn
        ]
      },

      {
        Sid    = "ReadObjects"
        Effect = "Allow"

        Action = [
          "s3:GetObject",
          "s3:GetObjectVersion"
        ]

        Resource = [
          "${aws_s3_bucket.buckets["transform"].arn}/*"
        ]
      }
    ]
  })
}