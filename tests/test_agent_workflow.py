import unittest

from app.agent.workflow import AgentWorkflow, WorkflowState
from app.agent.model_generation import ModelGenerationResult
from app.models.entities import RequirementContext
from app.models.entities import TestCase, TestPoint


class AgentWorkflowTest(unittest.TestCase):
    def test_workflow_runs_retrieve_points_and_cases_nodes(self):
        def retrieve(query):
            return ["历史缺陷: 重复手机号注册应阻止"]

        workflow = AgentWorkflow(retrieve_context=retrieve)
        state = WorkflowState(
            requirement=RequirementContext(
                markdown="# 用户注册\n手机号必填\n验证码错误时提示失败",
                supplemental="兼容 Chrome",
            ),
            use_rag=True,
        )

        result = workflow.run(state)

        self.assertEqual(result.executed_nodes, ["retrieve_context", "generate_test_points", "generate_test_cases"])
        self.assertIn("重复手机号注册应阻止", result.test_points[0].data_checks)
        self.assertEqual(result.test_cases[0].case_id, "TC-001")

    def test_workflow_uses_model_generation_when_available(self):
        class FakeModelGeneration:
            def generate(self, requirement):
                return ModelGenerationResult(
                    test_points=[TestPoint(module="模型模块", function="模型功能")],
                    test_cases=[
                        TestCase(
                            case_id="TC-900",
                            module="模型模块",
                            function="模型功能",
                            precondition="前置",
                            steps=["步骤"],
                            expected_results=["结果"],
                            priority="P0",
                            case_type="正向",
                        )
                    ],
                )

        workflow = AgentWorkflow(
            retrieve_context=lambda query: [],
            model_generation=FakeModelGeneration(),
        )

        result = workflow.run(WorkflowState(requirement=RequirementContext(markdown="# 需求"), use_rag=False))

        self.assertEqual(result.executed_nodes, ["generate_with_model"])
        self.assertEqual(result.test_points[0].module, "模型模块")
        self.assertEqual(result.test_cases[0].case_id, "TC-900")


if __name__ == "__main__":
    unittest.main()
