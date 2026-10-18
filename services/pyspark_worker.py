import sys
import os
import io
import time
import json
import traceback
from pathlib import Path

def init_spark():
    """Initializes high-performance local PySpark session."""
    from pyspark.sql import SparkSession
    
    # Dedicated local warehouse dir to avoid Hadoop permission conflicts on Windows
    warehouse_dir = Path.home() / ".practice_hub" / "spark_warehouse"
    warehouse_dir.mkdir(parents=True, exist_ok=True)
    warehouse_uri = warehouse_dir.as_uri()

    spark = (
        SparkSession.builder
        .master("local[2]")
        .appName("PracticeHubSession")
        .config("spark.ui.enabled", "false")
        .config("spark.driver.bindAddress", "127.0.0.1")
        .config("spark.driver.host", "127.0.0.1")
        .config("spark.sql.shuffle.partitions", "2")
        .config("spark.default.parallelism", "2")
        .config("spark.python.worker.reuse", "true")
        .config("spark.sql.adaptive.enabled", "false")
        .config("spark.sql.warehouse.dir", warehouse_uri)
        .config("spark.rdd.compress", "false")
        .config("spark.shuffle.compress", "false")
        .getOrCreate()
    )
    # Mute log4j noise to keep outputs clean
    spark.sparkContext.setLogLevel("ERROR")
    return spark

if __name__ == "__main__":
    # Ensure stdout/stderr are UTF-8
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

    try:
        spark = init_spark()
        # Warm up Python worker process and JVM JIT compilation
        try:
            _ = spark.createDataFrame([(1,)], ["_w"]).count()
        except Exception:
            pass
        # Notify parent process that worker is warm and ready
        sys.stdout.write(json.dumps({"type": "READY", "status": "WARM"}) + "\n")
        sys.stdout.flush()
    except Exception as e:
        sys.stdout.write(json.dumps({"type": "ERROR", "error": str(e)}) + "\n")
        sys.stdout.flush()
        sys.exit(1)

    worker_globals = {
        "__name__": "__main__",
        "spark": spark
    }

    while True:
        line = sys.stdin.readline()
        if not line:
            break
        try:
            req = json.loads(line)
        except Exception:
            continue

        action = req.get("action", "execute")
        req_id = req.get("req_id", "")

        if action == "stop":
            break

        if action == "reset":
            # Clear user variables except core objects
            worker_globals = {
                "__name__": "__main__",
                "spark": spark
            }
            # Resurrect SparkSession if it was stopped
            try:
                if spark.sparkContext._jsc is None:
                    spark = init_spark()
                    worker_globals["spark"] = spark
            except Exception:
                spark = init_spark()
                worker_globals["spark"] = spark

            sys.stdout.write(json.dumps({"type": "RESULT", "req_id": req_id, "status": "SUCCESS", "stdout": "Spark session reset.\n", "stderr": "", "duration_ms": 0}) + "\n")
            sys.stdout.flush()
            continue

        # Execute code
        code = req.get("code", "")
        start_time = time.time()
        buf_out = io.StringIO()
        buf_err = io.StringIO()
        orig_stdout = sys.stdout
        orig_stderr = sys.stderr
        status = "SUCCESS"

        sys.stdout = buf_out
        sys.stderr = buf_err

        try:
            # Check if active sparkContext is still valid
            try:
                if spark.sparkContext._jsc is None:
                    spark = init_spark()
                    worker_globals["spark"] = spark
            except Exception:
                spark = init_spark()
                worker_globals["spark"] = spark

            exec(code, worker_globals)
        except Exception:
            status = "FAILED"
            traceback.print_exc(file=buf_err)
        finally:
            sys.stdout = orig_stdout
            sys.stderr = orig_stderr

        duration_ms = int((time.time() - start_time) * 1000)
        res = {
            "type": "RESULT",
            "req_id": req_id,
            "status": status,
            "stdout": buf_out.getvalue(),
            "stderr": buf_err.getvalue(),
            "duration_ms": duration_ms
        }
        sys.stdout.write(json.dumps(res) + "\n")
        sys.stdout.flush()

    try:
        spark.stop()
    except Exception:
        pass
