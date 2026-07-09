import unittest

from app.agent.model_generation import ModelGenerationError, ModelGenerationService
from app.models.entities import RequirementContext


class FakeRouter:
    def __init__(self, content):
        self.content = content
        self.messages = None

    def chat(self, messages):
        self.messages = messages
        return self.content


class ModelGenerationTest(unittest.TestCase):
    def test_model_generation_parses_points_and_cases(self):
        router = FakeRouter(
            """
            {
              "test_points": [
                {
                  "module": "用户管理",
                  "function": "用户注册",
                  "positive_scenarios": ["手机号注册成功"],
                  "negative_scenarios": ["验证码错误时注册失败"],
                  "boundary_scenarios": ["手机号为空"],
                  "exception_scenarios": [],
                  "data_checks": ["重复手机号不可注册"],
                  "permission_checks": [],
                  "compatibility_notes": ["兼容 Chrome"]
                }
              ],
              "test_cases": [
                {
                  "case_id": "TC-001",
                  "module": "用户管理",
                  "function": "用户注册",
                  "precondition": "未注册用户",
                  "steps": ["打开注册页", "输入手机号"],
                  "expected_results": ["注册成功"],
                  "priority": "P0",
                  "case_type": "正向",
                  "remark": ""
                }
              ]
            }
            """
        )
        service = ModelGenerationService(router)

        result = service.generate(
            RequirementContext(
                markdown="# 用户管理\n用户注册",
                supplemental="兼容 Chrome",
                rag_context=["重复手机号不可注册"],
            )
        )

        self.assertEqual(result.test_points[0].module, "用户管理")
        self.assertEqual(result.test_cases[0].case_id, "TC-001")
        self.assertIn("只输出 JSON", router.messages[0].content)

    def test_model_generation_raises_clear_error_for_invalid_json(self):
        service = ModelGenerationService(FakeRouter("不是 JSON"))

        with self.assertRaisesRegex(ModelGenerationError, "模型输出不是合法 JSON"):
            service.generate(RequirementContext(markdown="# 用户管理\n用户注册"))


if __name__ == "__main__":
    unittest.main()
