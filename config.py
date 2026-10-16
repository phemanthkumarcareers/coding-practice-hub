import os
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent

DATABASE_DIR = BASE_DIR / "database"
DATABASE_DIR.mkdir(parents=True, exist_ok=True)
SQLITE_PATH = DATABASE_DIR / "app.db"
DUCKDB_PATH = DATABASE_DIR / "practice.duckdb"

UPLOADS_DIR = BASE_DIR / "uploads"
CSV_UPLOADS = UPLOADS_DIR / "csv"
JSON_UPLOADS = UPLOADS_DIR / "json"
PARQUET_UPLOADS = UPLOADS_DIR / "parquet"
for d in [CSV_UPLOADS, JSON_UPLOADS, PARQUET_UPLOADS]:
    d.mkdir(parents=True, exist_ok=True)

WORKSPACE_DIR = BASE_DIR / "workspace"
for tech in ["python", "sql", "pyspark", "databricks", "dsa"]:
    (WORKSPACE_DIR / tech).mkdir(parents=True, exist_ok=True)

LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

BACKUPS_DIR = BASE_DIR / "backups"
BACKUPS_DIR.mkdir(parents=True, exist_ok=True)

# Configuration Defaults
DEFAULT_SETTINGS = {
    "python_executable": "python",
    "java_home": os.environ.get("JAVA_HOME", ""),
    "spark_home": os.environ.get("SPARK_HOME", ""),
    "pyspark_config": "--master local[*]",
    "execution_timeout": "15",
    "theme": "dark",
    "autosave_interval": "15" # in seconds
}

TECHNOLOGIES = [
    "SQL",
    "Python",
    "PySpark",
    "Databricks",
    "DSA",
    "System Design"
]

STATUSES = [
    "NOT STARTED",
    "IN PROGRESS",
    "RUNNING",
    "SUCCESS",
    "FAILED",
    "COMPLETED"
]
