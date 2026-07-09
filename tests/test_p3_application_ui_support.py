import tempfile
import unittest
from pathlib import Path

from app.config.config_manager import ModelConfig
from app.models.entities import TestCase
from app.services.application_service import ApplicationService


class FakeHttpClient:
    def post_json(self, url, headers, payload):
        if url.endswith("/chat/completions"):
            return {"choices": [{"message": {"content": "ok"}}]}
        return {"message": {"content": "ok"}}


class P3ApplicationUiSupportTest(unittest.TestCase):
    def test_model_connection_test_uses_current_openai_compatible_config(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            service = ApplicationService(Path(temp_dir), http_client=FakeHttpClient())
            service.save_model_config(
                ModelConfig(
                    source="openai_compatible",
                    api_base_url="https://api.example.com/v1",
                    api_key="sk-test",
                    api_model="test-model",
                )
            )

            result = service.test_model_connection()

            self.assertTrue(result.ok)
            self.assertEqual(result.message, "连接成功")

    def test_export_cases_dispatches_by_format(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            service = ApplicationService(Path(temp_dir))
            service.current_cases = [
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

            markdown = service.export_cases("markdown")
            excel = service.export_cases("excel")

            self.assertEqual(markdown.suffix, ".md")
            self.assertEqual(excel.suffix, ".xlsx")

    def test_sync_cases_from_rows_updates_current_cases(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            service = ApplicationService(Path(temp_dir))

            service.sync_cases_from_rows(
                [
                    {
                        "case_id": "TC-009",
                        "module": "课程管理",
                        "function": "课程搜索",
                        "precondition": "存在课程",
                        "steps": "打开课程页\n输入关键词",
                        "expected_results": "展示匹配课程",
                        "priority": "P1",
                        "case_type": "正向",
                        "remark": "编辑后同步",
                    }
                ]
            )

            self.assertEqual(service.current_cases[0].case_id, "TC-009")
            self.assertEqual(service.current_cases[0].steps, ["打开课程页", "输入关键词"])
            self.assertEqual(service.current_cases[0].expected_results, ["展示匹配课程"])

    def test_rag_stats_returns_current_index_counts(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            knowledge = root / "history.md"
            knowledge.write_text("# 历史缺陷\n重复手机号注册应阻止", encoding="utf-8")
            service = ApplicationService(root)

            service.import_knowledge_document(knowledge)
            stats = service.rag_stats()

            self.assertEqual(stats.document_count, 1)
            self.assertGreaterEqual(stats.chunk_count, 1)


if __name__ == "__main__":
    unittest.main()
