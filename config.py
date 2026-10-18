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

def detect_java_home() -> str:
    """Auto-detect Java 17 / OpenJDK / Eclipse Adoptium installation directory."""
    if os.environ.get("JAVA_HOME") and Path(os.environ["JAVA_HOME"]).exists():
        return os.environ["JAVA_HOME"]
    candidates = [
        Path("C:/Program Files/Eclipse Adoptium"),
        Path("C:/Program Files/Java"),
        Path("C:/Program Files/Microsoft")
    ]
    for base in candidates:
        if base.exists():
            for sub in sorted(base.iterdir(), reverse=True):
                java_bin = sub / "bin" / ("java.exe" if os.name == "nt" else "java")
                if java_bin.exists():
                    return str(sub)
    return ""

def detect_spark_home() -> str:
    """Auto-detect PySpark / Spark installation directory."""
    if os.environ.get("SPARK_HOME") and Path(os.environ["SPARK_HOME"]).exists():
        return os.environ["SPARK_HOME"]
    try:
        import pyspark
        p = Path(pyspark.__file__).parent
        if p.exists():
            return str(p)
    except Exception:
        pass
    for p in [Path("C:/spark"), Path("C:/opt/spark"), Path("/opt/spark")]:
        if p.exists():
            return str(p)
    return ""

# Configuration Defaults
DEFAULT_SETTINGS = {
    "python_executable": "python",
    "java_home": detect_java_home(),
    "spark_home": detect_spark_home(),
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
