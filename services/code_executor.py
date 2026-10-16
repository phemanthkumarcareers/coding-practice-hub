import subprocess
import sys
import time
import uuid
import json
import shutil
from pathlib import Path
from config import WORKSPACE_DIR, DEFAULT_SETTINGS, SQLITE_PATH
from models.db import get_setting
import sqlite3

class CodeExecutor:
    def __init__(self):
        pass

    def _sync_datasets_to_workspace(self, target_dir: Path):
        """Copies or hardlinks all uploaded datasets to the execution workspace so they can be opened by filename."""
        try:
            conn = sqlite3.connect(SQLITE_PATH)
            conn.row_factory = sqlite3.Row
            datasets = conn.execute("SELECT original_name, file_path FROM datasets").fetchall()
            conn.close()

            for ds in datasets:
                src = Path(ds["file_path"])
                if src.exists():
                    dst = target_dir / ds["original_name"]
                    if not dst.exists() or dst.stat().st_mtime < src.stat().st_mtime:
                        shutil.copy2(src, dst)
        except Exception as e:
            print(f"Error syncing dataset files to workspace: {e}")

    def _get_dataset_paths_code(self):
        """Generates Python preamble dictionary exposing all uploaded datasets."""
        try:
            conn = sqlite3.connect(SQLITE_PATH)
            conn.row_factory = sqlite3.Row
            datasets = conn.execute("SELECT table_name, original_name, file_path, file_type FROM datasets").fetchall()
            conn.close()

            datasets_dict = {d["original_name"]: Path(d["file_path"]).as_posix() for d in datasets}
            table_dict = {d["table_name"]: Path(d["file_path"]).as_posix() for d in datasets}
            
            preamble = (
                "# === Preloaded Datasets Notice ===\n"
                "# All uploaded files are available directly in your working directory by filename!\n"
                "# Example: pd.read_csv('sample_employees.csv')\n"
                f"DATASETS = {json.dumps({**datasets_dict, **table_dict}, indent=2)}\n"
                "# =================================\n\n"
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

        # Sync datasets to workspace directory
        self._sync_datasets_to_workspace(target_dir)

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
            try:
                if script_file.exists():
                    script_file.unlink()
            except Exception:
                pass

        return result

code_executor = CodeExecutor()
