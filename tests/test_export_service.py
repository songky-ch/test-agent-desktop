import tempfile
import unittest
from pathlib import Path

from app.models.entities import TestCase
from app.services.export_service import ExportService


class ExportServiceTest(unittest.TestCase):
    def test_export_service_writes_markdown_cases(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            cases = [
                TestCase(
                    case_id="TC-001",
                    module="用户管理",
                    function="用户注册",
                    precondition="未注册用户",
                    steps=["打开注册页", "输入手机号"],
                    expected_results=["注册成功"],
                    priority="P0",
                    case_type="正向",
                    remark="",
                )
            ]

            output = ExportService(Path(temp_dir)).export_cases_markdown(cases, "cases.md")

            content = output.read_text(encoding="utf-8")
            self.assertEqual(output.name, "cases.md")
            self.assertIn(
                "| TC-001 | 用户管理 | 用户注册 | 未注册用户 | 打开注册页<br>输入手机号 | 注册成功 | P0 | 正向 |  |",
                content,
            )


if __name__ == "__main__":
    unittest.main()
