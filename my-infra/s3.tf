resource "aws_s3_bucket" "buckets" {
  for_each = var.s3_buckets

  bucket = each.value.name

  tags = {
    Name        = each.value.name
    Environment = each.value.environment
    ManagedBy   = "Terraform"
  }
}

# Versioning applies to ALL buckets automatically
resource "aws_s3_bucket_versioning" "buckets" {
  for_each = var.s3_buckets
  bucket   = aws_s3_bucket.buckets[each.key].id

  versioning_configuration {
    status = "Enabled"
  }
}

# Encryption applies to ALL buckets automatically
resource "aws_s3_bucket_server_side_encryption_configuration" "buckets" {
  for_each = var.s3_buckets
  bucket   = aws_s3_bucket.buckets[each.key].id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Public access block applies to ALL buckets automatically
resource "aws_s3_bucket_public_access_block" "buckets" {
  for_each = var.s3_buckets
  bucket   = aws_s3_bucket.buckets[each.key].id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Bucket policy — same policy applied to ALL buckets
resource "aws_s3_bucket_policy" "buckets" {
  for_each = var.s3_buckets
  bucket   = aws_s3_bucket.buckets[each.key].id

  depends_on = [aws_s3_bucket_public_access_block.buckets]

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowDataPipelineAccess"
        Effect = "Allow"
        Principal = {
          AWS = aws_iam_role.data_pipeline_role.arn
        }
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.buckets[each.key].arn,
          "${aws_s3_bucket.buckets[each.key].arn}/*"
        ]
      },
      {
        Sid       = "DenyNonHTTPS"
        Effect    = "Deny"
        Principal = "*"
        Action    = "s3:*"
        Resource = [
          aws_s3_bucket.buckets[each.key].arn,
          "${aws_s3_bucket.buckets[each.key].arn}/*"
        ]
        Condition = {
          Bool = { "aws:SecureTransport" = "false" }
        }
      }
    ]
  })
}