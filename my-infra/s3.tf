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
