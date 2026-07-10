import tempfile
import unittest
from pathlib import Path

from app.config.config_manager import ModelConfig
from app.services.application_service import ApplicationService


class ApplicationWorkflowTest(unittest.TestCase):
    def test_application_service_imports_knowledge_and_persists_generation_run(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            requirement = root / "requirement.txt"
            requirement.write_text("用户注册\n手机号必填\n验证码错误时提示失败", encoding="utf-8")
            knowledge = root / "history.md"
            knowledge.write_text("# 历史缺陷\n重复手机号注册应阻止", encoding="utf-8")
            service = ApplicationService(root)

            service.save_model_config(ModelConfig(source="ollama", ollama_model="qwen2:7b-instruct"))
            service.convert_document(requirement)
            stats = service.import_knowledge_document(knowledge)
            points = service.generate_test_points("兼容 Chrome 和 Edge", use_rag=True)
            cases = service.generate_test_cases()
            saved = service.persist_current_run("run-001")

            self.assertEqual(stats.document_count, 1)
            self.assertIn("重复手机号注册应阻止", points[0].data_checks)
            self.assertEqual(cases[0].case_id, "TC-001")
            self.assertTrue(saved.exists())

    def test_generation_requires_converted_markdown(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            service = ApplicationService(Path(temp_dir))

            with self.assertRaisesRegex(RuntimeError, "请先选择需求文档并转换 Markdown"):
                service.generate_test_points()

    def test_rule_fallback_uses_current_document_lines(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            requirement = root / "requirement.txt"
            requirement.write_text("# 课程报名\n登录后报名\n重复报名不允许\n支付超时提示失败", encoding="utf-8")
            service = ApplicationService(root)

            service.convert_document(requirement)
            points = service.generate_test_points("兼容移动端", use_rag=False, use_model=False)

            self.assertEqual(points[0].module, "课程报名")
            self.assertEqual(points[0].function, "登录后报名")
            self.assertEqual(points[1].function, "重复报名不允许")
            self.assertIn("兼容移动端", points[0].compatibility_notes)


if __name__ == "__main__":
    unittest.main()
