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


if __name__ == "__main__":
    unittest.main()
