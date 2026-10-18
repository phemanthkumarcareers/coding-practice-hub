import os
import sys
import subprocess
import time
import uuid
import json
import threading
import ctypes
import atexit
from pathlib import Path
from config import WORKSPACE_DIR, DEFAULT_SETTINGS
from models.db import get_setting

def _get_short_path(path_str: str) -> str:
    """Resolves Windows 8.3 short path name to avoid space issues in 'Program Files'."""
    if not path_str or sys.platform != "win32":
        return str(path_str) if path_str else ""
    try:
        buf = ctypes.create_unicode_buffer(500)
        res = ctypes.windll.kernel32.GetShortPathNameW(str(path_str), buf, 500)
        return buf.value if res > 0 and buf.value else str(path_str)
    except Exception:
        return str(path_str)

class PySparkService:
    def __init__(self):
        self._env_cache = None
        self._env_cache_time = 0
        self._worker_proc = None
        self._worker_lock = threading.Lock()
        self._is_warming_up = False
        atexit.register(self.shutdown)

    def shutdown(self):
        """Cleanly shuts down worker process and releases handles."""
        with self._worker_lock:
            if self._worker_proc:
                try:
                    self._worker_proc.stdin.write(json.dumps({"action": "stop"}) + "\n")
                    self._worker_proc.stdin.flush()
                except Exception:
                    pass
                try:
                    self._worker_proc.kill()
                except Exception:
                    pass
                self._worker_proc = None

    def check_environment(self, force_refresh: bool = False):
        """Diagnose local PySpark, Java and Spark setup with caching."""
        now = time.time()
        if not force_refresh and self._env_cache and (now - self._env_cache_time < 300):
            return dict(self._env_cache)

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

        # 3. Check Spark Home & Auto-discover if not explicitly set
        if not env_status["spark_home"]:
            try:
                import pyspark
                p = Path(pyspark.__file__).parent
                if p.exists():
                    env_status["spark_home"] = str(p)
            except Exception:
                pass
            if not env_status["spark_home"]:
                for sp in [Path("C:/spark"), Path("C:/opt/spark"), Path("/opt/spark")]:
                    if sp.exists():
                        env_status["spark_home"] = str(sp)
                        break

        env_status["detected_java_home"] = env_status.get("java_home", "")
        env_status["detected_spark_home"] = env_status.get("spark_home", "")

        self._env_cache = dict(env_status)
        self._env_cache_time = now
        return env_status

    def _build_worker_env(self, env_status: dict) -> dict:
        """Constructs an environment dict optimized for fast Windows PySpark execution."""
        env = os.environ.copy()
        raw_python = get_setting("python_executable", sys.executable) or sys.executable
        short_python = _get_short_path(raw_python)

        raw_java = env_status.get("java_home", "")
        short_java = _get_short_path(raw_java)

        if short_java:
            env["JAVA_HOME"] = short_java
            java_bin = str(Path(short_java) / "bin")
            env["PATH"] = java_bin + os.pathsep + env.get("PATH", "")

        if env_status.get("spark_home"):
            env["SPARK_HOME"] = env_status["spark_home"]

        env["PYSPARK_PYTHON"] = short_python
        env["PYSPARK_DRIVER_PYTHON"] = short_python
        env["PYSPARK_SUBMIT_ARGS"] = (
            "--conf spark.ui.enabled=false "
            "--conf spark.driver.bindAddress=127.0.0.1 "
            "--conf spark.driver.host=127.0.0.1 "
            "--conf spark.sql.shuffle.partitions=2 "
            "--conf spark.default.parallelism=2 "
            "pyspark-shell"
        )
        return env

    def _ensure_worker(self, env_status: dict) -> bool:
        """Starts the persistent warm PySpark worker daemon if not already running."""
        if self._worker_proc is not None:
            if self._worker_proc.poll() is None:
                return True
            else:
                self._worker_proc = None

        worker_script = Path(__file__).parent / "pyspark_worker.py"
        if not worker_script.exists():
            return False

        env = self._build_worker_env(env_status)
        python_bin = _get_short_path(get_setting("python_executable", sys.executable) or sys.executable)

        try:
            target_dir = WORKSPACE_DIR / "pyspark"
            target_dir.mkdir(parents=True, exist_ok=True)

            proc = subprocess.Popen(
                [python_bin, str(worker_script)],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                cwd=str(target_dir),
                env=env
            )

            # Read worker output until ready signal
            t_start = time.time()
            ready = False
            while time.time() - t_start < 40:
                line = proc.stdout.readline()
                if not line:
                    if proc.poll() is not None:
                        break
                    continue
                try:
                    msg = json.loads(line.strip())
                    if msg.get("type") == "READY":
                        ready = True
                        break
                    elif msg.get("type") == "ERROR":
                        break
                except Exception:
                    # Ignore initial non-JSON log banners if any
                    continue

            if ready and proc.poll() is None:
                self._worker_proc = proc
                return True
            else:
                try:
                    proc.kill()
                except Exception:
                    pass
                return False
        except Exception as e:
            print(f"Failed to start PySpark warm worker: {e}")
            return False

    def restart_session(self) -> dict:
        """Terminates active PySpark worker and starts a fresh warm session."""
        with self._worker_lock:
            if self._worker_proc:
                try:
                    self._worker_proc.stdin.write(json.dumps({"action": "stop"}) + "\n")
                    self._worker_proc.stdin.flush()
                except Exception:
                    pass
                try:
                    self._worker_proc.kill()
                except Exception:
                    pass
                self._worker_proc = None

            env_status = self.check_environment()
            if env_status["ready"]:
                started = self._ensure_worker(env_status)
                return {
                    "success": started,
                    "message": "PySpark session restarted successfully." if started else "Session stopped. Will re-initialize on next run."
                }
            return {"success": False, "message": "PySpark environment is not ready."}

    def warmup_background(self):
        """Asynchronously pre-warms the worker in the background."""
        if self._is_warming_up:
            return
        def _warm():
            self._is_warming_up = True
            try:
                env_status = self.check_environment()
                if env_status["ready"]:
                    with self._worker_lock:
                        self._ensure_worker(env_status)
            except Exception:
                pass
            finally:
                self._is_warming_up = False
        threading.Thread(target=_warm, daemon=True).start()

    def execute_pyspark(self, code: str, custom_timeout: int = None) -> dict:
        """Executes PySpark code via the fast persistent warm worker, with transparent fallback."""
        env_status = self.check_environment()

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
                    "3. Configure JAVA_HOME or SPARK_HOME in Settings\n"
                ),
                "status": "FAILED",
                "duration_ms": 0,
                "environment_missing": True
            }

        user_timeout = int(get_setting("execution_timeout", DEFAULT_SETTINGS["execution_timeout"]))
        timeout = custom_timeout or max(90, user_timeout * 3)

        # Attempt execution via warm worker under lock
        with self._worker_lock:
            if self._ensure_worker(env_status):
                req_id = uuid.uuid4().hex[:8]
                req = {"action": "execute", "req_id": req_id, "code": code}
                try:
                    self._worker_proc.stdin.write(json.dumps(req) + "\n")
                    self._worker_proc.stdin.flush()

                    # Read response with timeout handling
                    res_line = None
                    t_start = time.time()
                    while time.time() - t_start < timeout:
                        line = self._worker_proc.stdout.readline()
                        if not line:
                            if self._worker_proc.poll() is not None:
                                break
                            time.sleep(0.01)
                            continue
                        try:
                            data = json.loads(line.strip())
                            if data.get("type") == "RESULT" and data.get("req_id") == req_id:
                                res_line = data
                                break
                        except Exception:
                            continue

                    if res_line:
                        return {
                            "stdout": res_line.get("stdout", ""),
                            "stderr": res_line.get("stderr", ""),
                            "status": res_line.get("status", "SUCCESS"),
                            "duration_ms": res_line.get("duration_ms", 0),
                            "session_mode": "WARM"
                        }
                    else:
                        # Worker timed out or crashed; kill and reset
                        try:
                            self._worker_proc.kill()
                        except Exception:
                            pass
                        self._worker_proc = None
                        return {
                            "stdout": "",
                            "stderr": f"PySpark execution timed out after {timeout} seconds.",
                            "status": "FAILED",
                            "duration_ms": int((time.time() - t_start) * 1000),
                            "session_mode": "WARM"
                        }
                except Exception as ex:
                    try:
                        if self._worker_proc:
                            self._worker_proc.kill()
                    except Exception:
                        pass
                    self._worker_proc = None
                    print(f"PySpark worker communication error: {ex}, falling back to isolated run.")

        # Fallback to isolated one-shot execution if warm worker is unavailable
        return self._execute_isolated(code, env_status, timeout)

    def _execute_isolated(self, code: str, env_status: dict, timeout: int) -> dict:
        """One-shot isolated subprocess execution fallback."""
        start_time = time.time()
        python_bin = _get_short_path(get_setting("python_executable", sys.executable) or sys.executable)

        run_id = uuid.uuid4().hex[:8]
        target_dir = WORKSPACE_DIR / "pyspark"
        target_dir.mkdir(parents=True, exist_ok=True)
        script_file = target_dir / f"spark_run_{run_id}.py"

        env = self._build_worker_env(env_status)

        result = {
            "stdout": "",
            "stderr": "",
            "status": "SUCCESS",
            "duration_ms": 0,
            "session_mode": "ISOLATED"
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
