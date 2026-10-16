import subprocess
import sys
import time
import uuid
import json
from pathlib import Path
from config import WORKSPACE_DIR, DEFAULT_SETTINGS, SQLITE_PATH
from models.db import get_setting
import sqlite3

class CodeExecutor:
    def __init__(self):
        pass

    def _get_dataset_paths_code(self):
        """Generates Python preamble dictionary exposing all uploaded datasets."""
        try:
            conn = sqlite3.connect(SQLITE_PATH)
            conn.row_factory = sqlite3.Row
            datasets = conn.execute("SELECT table_name, file_path, file_type FROM datasets").fetchall()
            conn.close()
            
            datasets_dict = {d["table_name"]: Path(d["file_path"]).as_posix() for d in datasets}
            preamble = (
                "# === Preloaded Datasets Mapping ===\n"
                f"DATASETS = {json.dumps(datasets_dict, indent=2)}\n"
                "# Example usage: pd.read_csv(DATASETS['your_table']) if available\n"
                "# ==================================\n\n"
            )
            return preamble
        except Exception:
            return ""

    def execute_python(self, code: str, tech: str = "python", custom_timeout: int = None) -> dict:
        start_time = time.time()
        timeout = custom_timeout or int(get_setting("execution_timeout", DEFAULT_SETTINGS["execution_timeout"]))
        python_bin = get_setting("python_executable", sys.executable) or sys.executable

        run_id = uuid.uuid4().hex[:8]
        target_dir = WORKSPACE_DIR / tech.lower().replace(" ", "_")
        target_dir.mkdir(parents=True, exist_ok=True)
        script_file = target_dir / f"run_{run_id}.py"

        # Inject dataset dictionary helper preamble
        full_code = self._get_dataset_paths_code() + code

        result = {
            "stdout": "",
            "stderr": "",
            "status": "SUCCESS",
            "duration_ms": 0,
            "timed_out": False
        }

        try:
            with open(script_file, "w", encoding="utf-8") as f:
                f.write(full_code)

            # Run in isolated subprocess
            proc = subprocess.run(
                [python_bin, str(script_file)],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(target_dir)
            )

            result["stdout"] = proc.stdout
            result["stderr"] = proc.stderr
            if proc.returncode != 0:
                result["status"] = "FAILED"
            else:
                result["status"] = "SUCCESS"

        except subprocess.TimeoutExpired as e:
            result["status"] = "FAILED"
            result["timed_out"] = True
            result["stdout"] = e.stdout or ""
            result["stderr"] = f"Execution timed out after {timeout} seconds. Infinite loop or long-running process terminated."
        except Exception as e:
            result["status"] = "FAILED"
            result["stderr"] = f"Execution system error: {str(e)}"
        finally:
            result["duration_ms"] = int((time.time() - start_time) * 1000)
            # Clean up temporary script file
            try:
                if script_file.exists():
                    script_file.unlink()
            except Exception:
                pass

        return result

code_executor = CodeExecutor()
