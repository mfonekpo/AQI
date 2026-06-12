data "aws_caller_identity" "current" {}

resource "aws_sqs_queue" "dlq" {
  name = "${var.queue_name}-dlq"
}

resource "aws_sqs_queue" "my_queue" {
  name                       = var.queue_name
  delay_seconds              = 0
  max_message_size           = 262144
  message_retention_seconds  = 1209600 # 14 days
  receive_wait_time_seconds  = 10
  visibility_timeout_seconds = 120
  sqs_managed_sse_enabled    = true

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.dlq.arn
    maxReceiveCount     = 3
  })

  tags = {
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# Redrive Allow Policy for the Dead Letter Queue

resource "aws_sqs_queue_redrive_allow_policy" "my_queue_redrive_allow" {
  queue_url = aws_sqs_queue.dlq.id

  redrive_allow_policy = jsonencode({
    redrivePermission = "byQueue"
    sourceQueueArns   = [aws_sqs_queue.my_queue.arn]
  })
}


# ─── SQS Queue Policy ─────────────────────────────────

data "aws_iam_policy_document" "sqs_policy" {

  # Statement 1 — Queue Management (max 7 actions)
  statement {
    sid    = "AllowQueueManagement"
    effect = "Allow"

    principals {
      type        = "AWS"
      identifiers = ["arn:aws:iam::${data.aws_caller_identity.current.account_id}:user/aqi_user"]
    }

    actions = [
      "sqs:DeleteQueue",
      "sqs:GetQueueAttributes",
      "sqs:GetQueueUrl",
      "sqs:ListQueues",
      "sqs:SetQueueAttributes",
      "sqs:TagQueue",
      "sqs:UntagQueue"
    ]

    resources = [
      "arn:aws:sqs:${var.aws_region}:${data.aws_caller_identity.current.account_id}:${var.queue_name}",
      "arn:aws:sqs:${var.aws_region}:${data.aws_caller_identity.current.account_id}:${var.queue_name}-dlq"
    ]
  }

  # Statement 2 — Message Operations
  statement {
    sid    = "AllowMessageOperations"
    effect = "Allow"

    principals {
      type        = "AWS"
      identifiers = ["arn:aws:iam::${data.aws_caller_identity.current.account_id}:user/aqi_user"]
    }

    actions = [
      "sqs:SendMessage",
      "sqs:ReceiveMessage",
      "sqs:DeleteMessage",
      "sqs:ChangeMessageVisibility"
    ]

    resources = [
      "arn:aws:sqs:${var.aws_region}:${data.aws_caller_identity.current.account_id}:${var.queue_name}",
      "arn:aws:sqs:${var.aws_region}:${data.aws_caller_identity.current.account_id}:${var.queue_name}-dlq"
    ]
  }
}



# Give S3 permission to send messages to your SQS queue
data "aws_iam_policy_document" "s3_to_sqs" {
  statement {
    sid    = "AllowS3ToSendMessage"
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["s3.amazonaws.com"]
    }

    actions = ["sqs:SendMessage"]

    resources = [
      "arn:aws:sqs:${var.aws_region}:${data.aws_caller_identity.current.account_id}:${var.queue_name}"
    ]

    condition {
      test     = "ArnLike"
      variable = "aws:SourceArn"
      values   = ["arn:aws:s3:::aqi-staging"]
    }
  }
}

# Attach S3 permission to SQS queue policy
resource "aws_sqs_queue_policy" "s3_notification_policy" {
  queue_url = aws_sqs_queue.my_queue.id
  policy    = data.aws_iam_policy_document.s3_to_sqs.json
}

# S3 Event Notification → SQS
resource "aws_s3_bucket_notification" "staging_notification" {
  bucket = aws_s3_bucket.buckets["staging"].id

  queue {
    queue_arn = aws_sqs_queue.my_queue.arn
    events    = ["s3:ObjectCreated:*"] # Triggers on any new file
    # Optional: filter to specific prefix or suffix
    filter_prefix = "raw_data/"
    filter_suffix = ".json"
  }
  depends_on = [aws_sqs_queue_redrive_allow_policy.my_queue_redrive_allow]
}