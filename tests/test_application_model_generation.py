import tempfile
import unittest
from pathlib import Path

from app.config.config_manager import ModelConfig
from app.services.application_service import ApplicationService


class FakeHttpClient:
    def post_json(self, url, headers, payload):
        return {
            "choices": [
                {
                    "message": {
                        "content": """
                        {
                          "test_points": [
                            {
                              "module": "模型模块",
                              "function": "模型功能",
                              "positive_scenarios": [],
                              "negative_scenarios": [],
                              "boundary_scenarios": [],
                              "exception_scenarios": [],
                              "data_checks": [],
                              "permission_checks": [],
                              "compatibility_notes": []
                            }
                          ],
                          "test_cases": [
                            {
                              "case_id": "TC-777",
                              "module": "模型模块",
                              "function": "模型功能",
                              "precondition": "前置",
                              "steps": ["步骤"],
                              "expected_results": ["结果"],
                              "priority": "P0",
                              "case_type": "正向",
                              "remark": ""
                            }
                          ]
                        }
                        """
                    }
                }
            ]
        }


class ApplicationModelGenerationTest(unittest.TestCase):
    def test_application_service_can_enable_model_generation(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            req = root / "req.txt"
            req.write_text("用户注册\n手机号必填", encoding="utf-8")
            service = ApplicationService(root, http_client=FakeHttpClient())
            service.save_model_config(
                ModelConfig(
                    source="openai_compatible",
                    api_base_url="https://api.example.com/v1",
                    api_key="sk-test",
                    api_model="test-model",
                )
            )

            service.convert_document(req)
            points = service.generate_test_points(use_model=True)
            cases = service.generate_test_cases()

            self.assertEqual(points[0].module, "模型模块")
            self.assertEqual(cases[0].case_id, "TC-777")
            self.assertEqual(service.executed_nodes, ["retrieve_context", "generate_with_model"])


if __name__ == "__main__":
    unittest.main()
