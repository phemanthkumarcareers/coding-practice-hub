import os
import sys
import subprocess
import time
import uuid
from pathlib import Path
from config import WORKSPACE_DIR, DEFAULT_SETTINGS
from models.db import get_setting

class PySparkService:
    def check_environment(self):
        """Diagnose local PySpark, Java and Spark setup."""
        env_status = {
            "pyspark_installed": False,
            "pyspark_version": None,
            "java_installed": False,
            "java_version": None,
            "spark_home": get_setting("spark_home") or os.environ.get("SPARK_HOME", ""),
            "java_home": get_setting("java_home") or os.environ.get("JAVA_HOME", ""),
            "ready": False,
            "diagnostics": []
        }

        # 1. Check if pyspark python module is importable
        try:
            import pyspark
            env_status["pyspark_installed"] = True
            env_status["pyspark_version"] = getattr(pyspark, "__version__", "Available")
        except ImportError:
            env_status["diagnostics"].append("PySpark package is not installed in the Python environment (pip install pyspark).")

        # 2. Check Java & Auto-discover if not explicitly set
        if not env_status["java_home"]:
            search_dirs = [
                Path("C:/Program Files/Eclipse Adoptium"),
                Path("C:/Program Files/Java"),
                Path("C:/Program Files/Microsoft")
            ]
            for sdir in search_dirs:
                if sdir.exists():
                    for sub in sorted(sdir.iterdir(), reverse=True):
                        if (sub / "bin" / ("java.exe" if sys.platform == "win32" else "java")).exists():
                            env_status["java_home"] = str(sub)
                            break
                    if env_status["java_home"]:
                        break

        java_cmd = "java"
        if env_status["java_home"]:
            candidate = Path(env_status["java_home"]) / "bin" / ("java.exe" if sys.platform == "win32" else "java")
            if candidate.exists():
                java_cmd = str(candidate)

        try:
            res = subprocess.run([java_cmd, "-version"], capture_output=True, text=True, timeout=5)
            if res.returncode == 0 or "version" in (res.stderr or "").lower():
                env_status["java_installed"] = True
                first_line = (res.stderr or res.stdout).splitlines()[0] if (res.stderr or res.stdout) else "Java detected"
                env_status["java_version"] = first_line
        except Exception:
            env_status["diagnostics"].append("Java is not installed or not in PATH/JAVA_HOME. PySpark requires Java 8, 11, or 17.")

        if env_status["pyspark_installed"] and env_status["java_installed"]:
            env_status["ready"] = True

        return env_status

    def execute_pyspark(self, code: str, custom_timeout: int = None) -> dict:
        env_status = self.check_environment()
        
        # If Java or PySpark is missing, return friendly guidance without crashing
        if not env_status["ready"]:
            diag_text = "\n".join([f"• {d}" for d in env_status["diagnostics"]])
            return {
                "stdout": "",
                "stderr": (
                    "=== PySpark Environment Requirement Notice ===\n"
                    f"{diag_text}\n\n"
                    "PySpark requires:\n"
                    "1. Java (OpenJDK 11 or 17 recommended)\n"
                    "2. Python PySpark package (`pip install pyspark`)\n"
                    "3. Optionally configure JAVA_HOME or SPARK_HOME in Settings\n\n"
                    "Tip: You can practice Databricks and PySpark syntax anytime, and code is fully preserved!"
                ),
                "status": "FAILED",
                "duration_ms": 0,
                "environment_missing": True
            }

        start_time = time.time()
        user_timeout = int(get_setting("execution_timeout", DEFAULT_SETTINGS["execution_timeout"]))
        # PySpark JVM initialization + driver and DAG execution requires more startup time than standard Python scripts
        timeout = custom_timeout or max(90, user_timeout * 3)
        python_bin = get_setting("python_executable", sys.executable) or sys.executable

        run_id = uuid.uuid4().hex[:8]
        target_dir = WORKSPACE_DIR / "pyspark"
        target_dir.mkdir(parents=True, exist_ok=True)
        script_file = target_dir / f"spark_run_{run_id}.py"

        env = os.environ.copy()
        if env_status["java_home"]:
            env["JAVA_HOME"] = env_status["java_home"]
            java_bin = str(Path(env_status["java_home"]) / "bin")
            env["PATH"] = java_bin + os.pathsep + env.get("PATH", "")
        if env_status["spark_home"]:
            env["SPARK_HOME"] = env_status["spark_home"]

        # Ensure PySpark invokes the active Python binary rather than Windows alias
        env["PYSPARK_PYTHON"] = python_bin
        env["PYSPARK_DRIVER_PYTHON"] = python_bin

        # Speed up local Spark startup on Windows: skip web UI bind overhead and bind to localhost
        env["PYSPARK_SUBMIT_ARGS"] = "--conf spark.ui.enabled=false --conf spark.driver.bindAddress=127.0.0.1 pyspark-shell"

        result = {
            "stdout": "",
            "stderr": "",
            "status": "SUCCESS",
            "duration_ms": 0
        }

        try:
            with open(script_file, "w", encoding="utf-8") as f:
                f.write(code)

            proc = subprocess.run(
                [python_bin, str(script_file)],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(target_dir),
                env=env
            )

            result["stdout"] = proc.stdout
            if proc.returncode == 0:
                result["status"] = "SUCCESS"
                # If execution succeeded, do not pollute output with JVM/winutils/log4j warnings unless actual traceback occurred
                if proc.stderr and "Traceback" not in proc.stderr and "Exception" not in proc.stderr:
                    result["stderr"] = ""
                else:
                    result["stderr"] = proc.stderr
            else:
                result["status"] = "FAILED"
                result["stderr"] = proc.stderr
        except subprocess.TimeoutExpired as e:
            result["status"] = "FAILED"
            result["stdout"] = e.stdout or ""
            result["stderr"] = f"PySpark execution timed out after {timeout} seconds."
        except Exception as e:
            result["status"] = "FAILED"
            result["stderr"] = f"PySpark system error: {str(e)}"
        finally:
            result["duration_ms"] = int((time.time() - start_time) * 1000)
            try:
                if script_file.exists():
                    script_file.unlink()
            except Exception:
                pass

        return result

pyspark_service = PySparkService()
