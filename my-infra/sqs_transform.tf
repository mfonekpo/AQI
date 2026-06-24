# resource "aws_sqs_queue" "transform_dlq" {
#   name = "${var.transform_queue_name}-dlq"
# }

# resource "aws_sqs_queue" "transform_queue" {
#   name                       = var.transform_queue_name
#   delay_seconds              = 0
#   max_message_size           = 262144
#   message_retention_seconds  = 86400 # 24 hours
#   receive_wait_time_seconds  = 10
#   visibility_timeout_seconds = 30

#   redrive_policy = jsonencode({
#     deadLetterTargetArn = aws_sqs_queue.transform_dlq.arn
#     maxReceiveCount     = 3
#   })

#   tags = {
#     Environment = var.environment
#     ManagedBy   = "Terraform"
#   }
# }

# # Redrive Allow Policy for the Dead Letter Queue

# resource "aws_sqs_queue_redrive_allow_policy" "transform_queue_redrive_allow" {
#   queue_url = aws_sqs_queue.transform_dlq.id

#   redrive_allow_policy = jsonencode({
#     redrivePermission = "byQueue"
#     sourceQueueArns   = [aws_sqs_queue.transform_queue.arn]
#   })
# }


# # ─── SQS Queue Policy ─────────────────────────────────

# data "aws_iam_policy_document" "sqs_transform_policy" {

#   # Statement 1 — Queue Management (max 7 actions)
#   statement {
#     sid    = "AllowQueueManagement"
#     effect = "Allow"

#     principals {
#       type        = "AWS"
#       identifiers = ["arn:aws:iam::${data.aws_caller_identity.current.account_id}:user/aqi_user"]
#     }

#     actions = [
#       "sqs:DeleteQueue",
#       "sqs:GetQueueAttributes",
#       "sqs:GetQueueUrl",
#       "sqs:ListQueues",
#       "sqs:SetQueueAttributes",
#       "sqs:TagQueue",
#       "sqs:UntagQueue"
#     ]

#     resources = [
#       "arn:aws:sqs:${var.aws_region}:${data.aws_caller_identity.current.account_id}:${var.transform_queue_name}",
#       "arn:aws:sqs:${var.aws_region}:${data.aws_caller_identity.current.account_id}:${var.transform_queue_name}-dlq"
#     ]
#   }


#   # Statement 2 — Message Operations
#   statement {
#     sid    = "AllowMessageOperations"
#     effect = "Allow"

#     principals {
#       type        = "AWS"
#       identifiers = ["arn:aws:iam::${data.aws_caller_identity.current.account_id}:user/aqi_user"]
#     }

#     actions = [
#       "sqs:SendMessage",
#       "sqs:ReceiveMessage",
#       "sqs:DeleteMessage",
#       "sqs:ChangeMessageVisibility"
#     ]

#     resources = [
#       "arn:aws:sqs:${var.aws_region}:${data.aws_caller_identity.current.account_id}:${var.transform_queue_name}",
#       "arn:aws:sqs:${var.aws_region}:${data.aws_caller_identity.current.account_id}:${var.transform_queue_name}-dlq"
#     ]
#   }
# }


# # Give S3 permission to send messages to your SQS queue
# data "aws_iam_policy_document" "s3_transform_to_sqs" {
#   statement {
#     sid    = "AllowS3ToSendMessages"
#     effect = "Allow"

#     principals {
#       type        = "Service"
#       identifiers = ["s3.amazonaws.com"]
#     }
#     actions = ["sqs:SendMessage"]

#     resources = [
#       "arn:aws:sqs:${var.aws_region}:${data.aws_caller_identity.current.account_id}:${var.transform_queue_name}"
#     ]

#     condition {
#       test     = "ArnLike"
#       variable = "aws:SourceArn"
#       values   = ["arn:aws:s3:::${var.s3_buckets.transform.name}"]
#     }
#   }
# }


# resource "aws_sqs_queue_policy" "transform_queue_policy" {
#   queue_url = aws_sqs_queue.transform_queue.id
#   policy    = data.aws_iam_policy_document.s3_transform_to_sqs.json
# }

# S3 Event Notification → SQS
# resource "aws_s3_bucket_notification" "transform_notification" {
#   bucket = aws_s3_bucket.buckets["transform"].id

#   queue {
#     id            = "TransformQueueNotification"
#     queue_arn     = aws_sqs_queue.transform_queue.arn
#     events        = ["s3:ObjectCreated:*"]
#     filter_prefix = "transformed_data/"
#     filter_suffix = ".parquet"
#   }
#   depends_on = [aws_sqs_queue_policy.transform_queue_policy]
# }