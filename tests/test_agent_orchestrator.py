import unittest

from app.agent.orchestrator import AgentOrchestrator
from app.models.entities import RequirementContext


class AgentOrchestratorTest(unittest.TestCase):
    def test_agent_generates_test_points_from_requirement_context(self):
        context = RequirementContext(
            markdown="# 用户注册\n手机号必填\n验证码错误时提示失败",
            supplemental="兼容 Chrome 和 Edge, 登录响应小于 2s",
            rag_context=["历史缺陷: 重复手机号注册应阻止"],
        )

        points = AgentOrchestrator().generate_test_points(context)

        self.assertEqual(points[0].module, "用户注册")
        self.assertEqual(points[0].function, "手机号必填")
        self.assertIn("验证码错误时提示失败", points[0].negative_scenarios)
        self.assertIn("兼容 Chrome 和 Edge", points[0].compatibility_notes)
        self.assertIn("重复手机号注册应阻止", points[0].data_checks)

    def test_agent_generates_cases_from_test_points(self):
        context = RequirementContext(markdown="# 用户登录\n支持手机号登录")
        orchestrator = AgentOrchestrator()
        points = orchestrator.generate_test_points(context)

        cases = orchestrator.generate_test_cases(points)

        self.assertEqual(cases[0].case_id, "TC-001")
        self.assertEqual(cases[0].module, "用户登录")
        self.assertEqual(cases[0].function, "支持手机号登录")
        self.assertEqual(cases[0].priority, "P1")


if __name__ == "__main__":
    unittest.main()
