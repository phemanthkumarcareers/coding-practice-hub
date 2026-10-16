import unittest
import os
import json
from datetime import date
from app import create_app
from models.db import (
    init_db,
    get_connection,
    get_or_create_daily_session,
    update_session_completion_status,
    TECHNOLOGIES
)
from services.duckdb_service import duckdb_service
from services.code_executor import code_executor
from services.streak_service import streak_service
from services.backup_service import backup_service

class TestCodingPracticeHub(unittest.TestCase):
    @classmethod
    def cleanup_test_data(cls):
        import glob
        # 1. Clean SQLite test sessions and practices
        try:
            conn = get_connection()
            conn.execute("DELETE FROM daily_sessions WHERE date LIKE '2099-%';")
            conn.commit()
            conn.close()
        except Exception:
            pass

        # 2. Clean DuckDB test table
        try:
            duckdb_service.execute_query("DROP TABLE IF EXISTS test_col_size_tbl;")
        except Exception:
            pass

        # 3. Clean user_dbs test databases
        for f in glob.glob("database/user_dbs/test_db_*.duckdb*"):
            try:
                os.remove(f)
            except Exception:
                pass

        # 4. Clean backup zip files created during tests
        for b in glob.glob("backups/coding_practice_backup_*.zip"):
            try:
                os.remove(b)
            except Exception:
                pass

    @classmethod
    def setUpClass(cls):
        cls.cleanup_test_data()
        init_db()
        cls.app = create_app()
        cls.client = cls.app.test_client()

    @classmethod
    def tearDownClass(cls):
        cls.cleanup_test_data()

    def test_01_database_initialization(self):
        conn = get_connection()
        tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        conn.close()
        
        expected_tables = ["daily_sessions", "practices", "executions", "datasets", "tags", "practice_tags", "settings"]
        for t in expected_tables:
            self.assertIn(t, tables, f"Table {t} should be initialized")

    def test_02_daily_session_and_six_practices(self):
        test_date = "2026-10-17"
        session = get_or_create_daily_session(test_date)
        
        self.assertEqual(session["date"], test_date)
        self.assertEqual(len(session["practices"]), 6, "Every session must have exactly 6 practices")
        
        techs_in_session = [p["technology"] for p in session["practices"]]
        for t in TECHNOLOGIES:
            self.assertIn(t, techs_in_session)

    def test_03_prevent_duplicate_sessions(self):
        test_date = "2026-10-17"
        session1 = get_or_create_daily_session(test_date)
        session2 = get_or_create_daily_session(test_date)
        self.assertEqual(session1["id"], session2["id"], "Multiple calls for the same date must return the same session")

    def test_04_python_execution_success_and_failure(self):
        # 1. Success case
        code_success = "print('Subprocess execution output: 42')"
        res_ok = code_executor.execute_python(code_success, tech="python")
        self.assertEqual(res_ok["status"], "SUCCESS")
        self.assertIn("Subprocess execution output: 42", res_ok["stdout"])
        self.assertEqual(res_ok["stderr"], "")

        # 2. Failure case
        code_fail = "x = 1 / 0"
        res_fail = code_executor.execute_python(code_fail, tech="python")
        self.assertEqual(res_fail["status"], "FAILED")
        self.assertIn("ZeroDivisionError", res_fail["stderr"])

        # 3. Timeout handling
        code_timeout = "import time; time.sleep(5)"
        res_timeout = code_executor.execute_python(code_timeout, tech="python", custom_timeout=1)
        self.assertEqual(res_timeout["status"], "FAILED")
        self.assertTrue(res_timeout["timed_out"])

    def test_05_duckdb_sql_execution(self):
        # Test basic query
        res = duckdb_service.execute_query("SELECT 100 AS num, 'DuckDB' AS engine;")
        self.assertEqual(res["status"], "SUCCESS")
        self.assertEqual(res["columns"], ["num", "engine"])
        self.assertEqual(res["rows"], [[100, "DuckDB"]])
        self.assertEqual(res["row_count"], 1)

        # Test window function & CTE
        cte_query = """
            WITH ranked AS (
                SELECT 1 AS id, 10 AS score
                UNION ALL
                SELECT 2 AS id, 20 AS score
            )
            SELECT id, score, RANK() OVER (ORDER BY score DESC) as rank
            FROM ranked;
        """
        res_cte = duckdb_service.execute_query(cte_query)
        self.assertEqual(res_cte["status"], "SUCCESS")
        self.assertEqual(len(res_cte["rows"]), 2)

        # Test SQL Error handling
        res_err = duckdb_service.execute_query("SELECT * FROM non_existent_table_xyz;")
        self.assertEqual(res_err["status"], "FAILED")
        self.assertIsNotNone(res_err["error"])

    def test_06_execution_history_preservation(self):
        import uuid
        test_date = f"2099-01-{uuid.uuid4().hex[:4]}"
        session = get_or_create_daily_session(test_date)
        sql_practice = next(p for p in session["practices"] if p["technology"] == "SQL")

        # Run 1: Failed
        res1 = self.client.post("/api/practice/run", json={
            "id": sql_practice["id"],
            "technology": "SQL",
            "code": "SELECT * FROM non_existent;"
        })
        self.assertEqual(res1.status_code, 200)

        # Run 2: Success
        res2 = self.client.post("/api/practice/run", json={
            "id": sql_practice["id"],
            "technology": "SQL",
            "code": "SELECT 1;"
        })
        self.assertEqual(res2.status_code, 200)

        # Check execution history: both must be preserved
        hist_res = self.client.get(f"/api/practice/executions/{sql_practice['id']}")
        self.assertEqual(hist_res.status_code, 200)
        executions = hist_res.get_json()
        self.assertEqual(len(executions), 2, "Both executions must be preserved")
        self.assertEqual(executions[0]["status"], "SUCCESS")
        self.assertEqual(executions[1]["status"], "FAILED")

    def test_07_completion_logic_0_to_6(self):
        import uuid
        test_date = f"2099-02-{uuid.uuid4().hex[:4]}"
        session = get_or_create_daily_session(test_date)
        session_id = session["id"]

        # Mark all 6 as COMPLETED one by one
        for i, p in enumerate(session["practices"], 1):
            save_res = self.client.post("/api/practice/save", json={
                "id": p["id"],
                "status": "COMPLETED",
                "title": f"Done {p['technology']}"
            })
            data = save_res.get_json()
            self.assertEqual(data["completed_count"], i)
            if i == 6:
                self.assertEqual(data["session_status"], "COMPLETED")
            else:
                self.assertEqual(data["session_status"], "IN PROGRESS")

    def test_08_global_search(self):
        import uuid
        test_date = f"2099-04-{uuid.uuid4().hex[:4]}"
        session = get_or_create_daily_session(test_date)
        p = session["practices"][0]
        self.client.post("/api/practice/save", json={
            "id": p["id"],
            "title": "Quantum Window Function Practice",
            "question": "Calculate running totals using partition by",
            "topic": "Analytics"
        })

        search_res = self.client.get("/api/search?q=Quantum")
        results = search_res.get_json()["results"]
        self.assertTrue(any(r["title"] == "Quantum Window Function Practice" for r in results))

    def test_09_backup_service(self):
        backup_file = backup_service.create_backup()
        self.assertTrue(backup_file.exists())
        self.assertTrue(backup_file.name.endswith(".zip"))

    def test_10_multifile_execution(self):
        import uuid
        test_date = f"2099-03-{uuid.uuid4().hex[:4]}"
        session = get_or_create_daily_session(test_date)
        py_practice = next(p for p in session["practices"] if p["technology"] == "Python")

        # Multi-file Python execution
        files = {
            "helper.py": "def greet(name):\n    return f'Hello, {name}!'\n",
            "main.py": "from helper import greet\nprint(greet('Engineer'))\n"
        }
        res = self.client.post("/api/practice/run", json={
            "id": py_practice["id"],
            "technology": "Python",
            "files": files,
            "entry_file": "main.py"
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["status"], "SUCCESS")
        self.assertIn("Hello, Engineer!", data["output"])

    def test_11_explorer_schema_with_column_sizes(self):
        # Create a test table in DuckDB
        duckdb_service.execute_query("CREATE OR REPLACE TABLE test_col_size_tbl (id BIGINT, name VARCHAR(100), is_active BOOLEAN);")
        schemas = duckdb_service.get_explorer_schema()
        target = next((s for s in schemas if s["name"] == "test_col_size_tbl"), None)
        self.assertIsNotNone(target, "test_col_size_tbl must appear in explorer schemas")
        cols = {c["name"]: c for c in target["columns"]}
        self.assertIn("id", cols)
        self.assertEqual(cols["id"]["size"], "8 bytes")
        self.assertIn(cols["name"]["size"], ["variable", "max 100 chars"])
        self.assertIn("is_active", cols)
        self.assertEqual(cols["is_active"]["size"], "1 byte")

    def test_12_create_database(self):
        import uuid
        db_name = f"test_db_{uuid.uuid4().hex[:6]}"
        res = self.client.post("/api/practice/create_database", json={"name": db_name})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["database"], db_name)

        # Verify listed in databases
        list_res = self.client.get("/api/practice/databases")
        dbs = list_res.get_json()["databases"]
        self.assertTrue(any(d["name"] == db_name for d in dbs))

    def test_13_pyspark_execution(self):
        import uuid
        from services.pyspark_service import pyspark_service
        env_check = pyspark_service.check_environment()
        self.assertTrue(env_check["ready"], f"PySpark environment must be ready: {env_check['diagnostics']}")
        
        # Test basic execution
        code = "print('PySpark Test OK')"
        res = pyspark_service.execute_pyspark(code)
        self.assertEqual(res["status"], "SUCCESS")
        self.assertIn("PySpark Test OK", res["stdout"])

if __name__ == "__main__":
    unittest.main()


