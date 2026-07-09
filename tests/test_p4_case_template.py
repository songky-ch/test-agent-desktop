import tempfile
import unittest
from pathlib import Path

from app.agent.model_generation import ModelGenerationService
from app.models.entities import CaseTemplate, RequirementContext, TestCase
from app.services.application_service import ApplicationService


class FakeRouter:
    def __init__(self):
        self.messages = None

    def chat(self, messages):
        self.messages = messages
        return '{"test_points": [], "test_cases": []}'


class P4CaseTemplateTest(unittest.TestCase):
    def test_sync_points_from_rows_updates_cases_generated_after_review(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            service = ApplicationService(Path(temp_dir))
            service.sync_points_from_rows(
                [
                    {
                        "module": "课程管理",
                        "function": "课程搜索",
                        "positive_scenarios": "按关键词搜索成功",
                        "negative_scenarios": "无匹配结果时提示为空",
                        "boundary_scenarios": "",
                        "exception_scenarios": "",
                        "data_checks": "只展示有权限课程",
                        "permission_checks": "",
                        "compatibility_notes": "",
                    }
                ]
            )

            cases = service.generate_test_cases()

            self.assertEqual(cases[0].module, "课程管理")
            self.assertEqual(cases[0].function, "课程搜索")
            self.assertIn("无匹配结果时提示为空", cases[0].remark)

    def test_export_markdown_uses_case_template_fields_and_order(self):
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
                    remark="",
                )
            ]
            service.save_case_template(["用例编号", "所属模块", "功能点", "优先级"])

            output = service.export_cases("markdown")

            content = output.read_text(encoding="utf-8")
            self.assertIn("| 用例编号 | 所属模块 | 功能点 | 优先级 |", content)
            self.assertIn("| TC-001 | 用户管理 | 用户注册 | P0 |", content)
            self.assertNotIn("测试步骤", content)

    def test_model_generation_prompt_contains_template_fields(self):
        router = FakeRouter()
        service = ModelGenerationService(
            router,
            CaseTemplate(fields=["case_id", "module", "function", "priority"]),
        )

        service.generate(RequirementContext(markdown="# 用户管理\n用户注册"))

        self.assertIn("用例编号, 所属模块, 功能点, 优先级", router.messages[0].content)


if __name__ == "__main__":
    unittest.main()
