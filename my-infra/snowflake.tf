# --------------------- Create the database -----------------------
resource "snowflake_database" "tf_aqi_db" {
  name                            = var.db_name
  comment                         = "terraform provisioned database for the aqi project"
  is_transient                    = false
  suspend_task_after_num_failures = 4
  task_auto_retry_attempts        = 4
}

# --------------- Create the data warehouse --------------------
resource "snowflake_warehouse" "tf_aqi_warehouse" {
  name                      = var.warehouse_name
  comment                   = "terraform provisioned warehouse for the aqi project"
  warehouse_type            = "STANDARD"
  warehouse_size            = "XSMALL"
  max_cluster_count         = 1
  min_cluster_count         = 1
  auto_suspend              = 60
  auto_resume               = true
  enable_query_acceleration = false
  initially_suspended       = true
}

# --------------- Create the schema --------------------
# resource "snowflake_schema" "tf_aqi_schema" {
#   name                            = var.schema_name
#   comment                         = "terraform provisioned schema for the aqi project"
#   database                        = snowflake_database.tf_aqi_db.name
#   is_transient                    = false
#   task_auto_retry_attempts        = 4
#   suspend_task_after_num_failures = 4
# }

# --------------- storage integration --------------------
resource "snowflake_storage_integration_aws" "tf_s3_integration" {
  name                      = var.s3_storage_name
  comment                   = "terraform provisioned storage integration for the aqi project"
  enabled                   = true
  storage_provider          = "S3"
  storage_aws_role_arn      = aws_iam_role.snowflake_storage_role.arn
  storage_allowed_locations = ["s3://${var.s3_buckets.transform.name}"]
}

# ----------------------- configure file format for snowflake --------------------
resource "snowflake_file_format" "tf_snowflake_file_format" {
  name        = "file_format"
  database    = var.db_name
  schema      = var.schema_name
  format_type = "PARQUET"
}

# --------------------- configure snowflake stage --------------------
resource "snowflake_stage_external_s3" "tf_snowflake_stage" {
  name                = "snowflake_storage_stage"
  comment             = "terraform provisioned stage for the aqi project"
  url                 = "s3://${var.s3_buckets.transform.name}/transformed_data/"
  database            = var.db_name
  schema              = var.schema_name
  storage_integration = snowflake_storage_integration_aws.tf_s3_integration.name

  directory {
    enable = false
  }
}

# ---------- configure snowflake pipeline -----------
resource "snowflake_pipe" "tf_snowflake_pipe" {
  name        = "aqi_pipe"
  database    = var.db_name
  schema      = var.schema_name
  comment     = "terraform provisioned pipe for the aqi project"
  auto_ingest = true

  copy_statement = <<EOF
  COPY INTO
    ${var.db_name}.${var.schema_name}.${var.table_name}

  FROM
    @${snowflake_stage_external_s3.tf_snowflake_stage.fully_qualified_name}

  FILE_FORMAT = (
    FORMAT_NAME = '${snowflake_file_format.tf_snowflake_file_format.fully_qualified_name}'
  )

  MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE
  EOF

  lifecycle {
    replace_triggered_by = [
      snowflake_stage_external_s3.tf_snowflake_stage.url,
      snowflake_stage_external_s3.tf_snowflake_stage.storage_integration,
      snowflake_stage_external_s3.tf_snowflake_stage.encryption,
    ]
  }
}
