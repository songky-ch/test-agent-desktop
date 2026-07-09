import tempfile
import unittest
from pathlib import Path

from app.models.entities import TestCase, TestPoint
from app.services.result_store import ResultStore


class ResultStoreTest(unittest.TestCase):
    def test_result_store_persists_points_and_cases(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            store = ResultStore(Path(temp_dir))
            points = [TestPoint(module="用户管理", function="用户注册")]
            cases = [
                TestCase(
                    case_id="TC-001",
                    module="用户管理",
                    function="用户注册",
                    precondition="未注册用户",
                    steps=["打开注册页"],
                    expected_results=["注册成功"],
                    priority="P0",
                    case_type="正向",
                )
            ]

            saved = store.save_run("run-001", points, cases)
            loaded = store.load_run("run-001")

            self.assertTrue(saved.exists())
            self.assertEqual(loaded["test_points"][0]["module"], "用户管理")
            self.assertEqual(loaded["test_cases"][0]["case_id"], "TC-001")


if __name__ == "__main__":
    unittest.main()
