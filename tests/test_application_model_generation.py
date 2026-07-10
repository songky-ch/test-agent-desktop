import tempfile
import unittest
from pathlib import Path

from app.config.config_manager import ModelConfig
from app.services.application_service import ApplicationService


class FakeHttpClient:
    def __init__(self):
        self.payload = None
        self.payloads = []

    def post_json(self, url, headers, payload):
        self.payload = payload
        self.payloads.append(payload)
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
            client = FakeHttpClient()
            service = ApplicationService(root, http_client=client)
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
            self.assertEqual(service.executed_nodes, ["retrieve_context", "generate_test_points_with_model"])
            self.assertIn("手机号必填", client.payloads[0]["messages"][1]["content"])
            self.assertIn("模型功能", client.payloads[1]["messages"][1]["content"])

    def test_supplemental_input_is_sent_to_model_prompt(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            req = root / "req.txt"
            req.write_text("课程报名", encoding="utf-8")
            client = FakeHttpClient()
            service = ApplicationService(root, http_client=client)
            service.save_model_config(
                ModelConfig(
                    source="openai_compatible",
                    api_base_url="https://api.example.com/v1",
                    api_key="sk-test",
                    api_model="test-model",
                )
            )

            service.convert_document(req)
            service.generate_test_points("补充: 重点覆盖重复报名和支付超时", use_model=True)

            self.assertIn("重复报名", client.payload["messages"][1]["content"])
            self.assertIn("支付超时", client.payload["messages"][1]["content"])


if __name__ == "__main__":
    unittest.main()
