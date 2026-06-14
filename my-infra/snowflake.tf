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
  name                      = "aqi_dwh"
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
resource "snowflake_schema" "tf_aqi_schema" {
  name                            = var.schema_name
  comment                         = "terraform provisioned schema for the aqi project"
  database                        = snowflake_database.tf_aqi_db.name
  is_transient                    = false
  task_auto_retry_attempts        = 4
  suspend_task_after_num_failures = 4
}
