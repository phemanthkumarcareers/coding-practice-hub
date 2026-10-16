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
        """Copies or links all uploaded datasets directly to the execution workspace."""
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

    def execute_python_project(self, files: dict, entry_file: str = "main.py", tech: str = "python", custom_timeout: int = None) -> dict:
        """
        Executes a multi-file Python project.
        files: dict mapping filename -> code content, e.g. {"main.py": "...", "utils.py": "..."}
        entry_file: the file to execute (defaults to "main.py")
        """
        start_time = time.time()
        timeout = custom_timeout or int(get_setting("execution_timeout", DEFAULT_SETTINGS["execution_timeout"]))
        python_bin = get_setting("python_executable", sys.executable) or sys.executable

        run_id = uuid.uuid4().hex[:8]
        target_dir = WORKSPACE_DIR / tech.lower().replace(" ", "_") / f"project_{run_id}"
        target_dir.mkdir(parents=True, exist_ok=True)

        # Sync datasets directly into project folder so pd.read_csv('filename.csv') works everywhere
        self._sync_datasets_to_workspace(target_dir)

        result = {
            "stdout": "",
            "stderr": "",
            "status": "SUCCESS",
            "duration_ms": 0,
            "timed_out": False
        }

        try:
            # Write all project files to directory
            for fname, content in files.items():
                safe_fname = Path(fname).name
                file_path = target_dir / safe_fname
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)

            target_script = target_dir / entry_file
            if not target_script.exists():
                # Fallback to first python file in dict
                py_files = [f for f in files.keys() if f.endswith(".py")]
                entry_file = py_files[0] if py_files else "main.py"
                target_script = target_dir / entry_file

            # Run in isolated subprocess with cwd set to project folder
            proc = subprocess.run(
                [python_bin, str(target_script)],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(target_dir)
            )

            result["stdout"] = proc.stdout
            result["stderr"] = proc.stderr
            result["status"] = "SUCCESS" if proc.returncode == 0 else "FAILED"

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
            # Clean up temporary execution directory
            try:
                if target_dir.exists():
                    shutil.rmtree(target_dir, ignore_errors=True)
            except Exception:
                pass

        return result

    def execute_python(self, code: str, tech: str = "python", custom_timeout: int = None) -> dict:
        """Backward-compatible single-file execution wrapper."""
        return self.execute_python_project({"main.py": code}, entry_file="main.py", tech=tech, custom_timeout=custom_timeout)

code_executor = CodeExecutor()
