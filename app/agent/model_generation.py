import json
from dataclasses import dataclass

from app.agent.llm_provider import LlmMessage, ModelRouter
from app.models.entities import CaseTemplate, RequirementContext, TestCase, TestPoint
from app.services.export_service import DEFAULT_CASE_TEMPLATE, case_template_labels


class ModelGenerationError(RuntimeError):
    pass


@dataclass(frozen=True)
class ModelGenerationResult:
    test_points: list[TestPoint]
    test_cases: list[TestCase]


class ModelGenerationService:
    def __init__(self, router: ModelRouter, case_template: CaseTemplate = DEFAULT_CASE_TEMPLATE):
        self.router = router
        self.case_template = case_template

    def generate(self, context: RequirementContext) -> ModelGenerationResult:
        content = self.router.chat(self._messages(context))
        payload = self._parse_json(content)
        return ModelGenerationResult(
            test_points=[self._parse_point(item) for item in payload.get("test_points", [])],
            test_cases=[self._parse_case(item) for item in payload.get("test_cases", [])],
        )

    def _messages(self, context: RequirementContext) -> list[LlmMessage]:
        prompt = (
            "你是测试人员专属 AI Agent。请基于需求文档、补充需求和 RAG 上下文生成测试点和测试用例。\n"
            "只输出 JSON, 不要输出 Markdown, 不要解释。\n"
            "JSON 结构必须包含 test_points 和 test_cases 两个数组。\n"
            "test_points 字段: module, function, positive_scenarios, negative_scenarios, "
            "boundary_scenarios, exception_scenarios, data_checks, permission_checks, compatibility_notes。\n"
            "test_cases 字段: case_id, module, function, precondition, steps, expected_results, "
            "priority, case_type, remark。\n"
            f"当前用户用例模板字段顺序: {', '.join(case_template_labels(self.case_template))}。\n"
        )
        user = (
            f"需求文档:\n{context.markdown}\n\n"
            f"补充需求:\n{context.supplemental}\n\n"
            f"RAG 上下文:\n{chr(10).join(context.rag_context)}"
        )
        return [
            LlmMessage(role="system", content=prompt),
            LlmMessage(role="user", content=user),
        ]

    def _parse_json(self, content: str) -> dict:
        cleaned = content.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.strip("`")
            if cleaned.startswith("json"):
                cleaned = cleaned[4:].strip()
        try:
            payload = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            raise ModelGenerationError("模型输出不是合法 JSON") from exc
        if not isinstance(payload, dict):
            raise ModelGenerationError("模型输出 JSON 顶层必须是对象")
        return payload

    def _parse_point(self, item: dict) -> TestPoint:
        return TestPoint(
            module=str(item.get("module", "")),
            function=str(item.get("function", "")),
            positive_scenarios=self._list(item.get("positive_scenarios")),
            negative_scenarios=self._list(item.get("negative_scenarios")),
            boundary_scenarios=self._list(item.get("boundary_scenarios")),
            exception_scenarios=self._list(item.get("exception_scenarios")),
            data_checks=self._list(item.get("data_checks")),
            permission_checks=self._list(item.get("permission_checks")),
            compatibility_notes=self._list(item.get("compatibility_notes")),
        )

    def _parse_case(self, item: dict) -> TestCase:
        return TestCase(
            case_id=str(item.get("case_id", "")),
            module=str(item.get("module", "")),
            function=str(item.get("function", "")),
            precondition=str(item.get("precondition", "")),
            steps=self._list(item.get("steps")),
            expected_results=self._list(item.get("expected_results")),
            priority=str(item.get("priority", "")),
            case_type=str(item.get("case_type", "")),
            remark=str(item.get("remark", "")),
        )

    def _list(self, value) -> list[str]:
        if value is None:
            return []
        if isinstance(value, list):
            return [str(item) for item in value]
        return [str(value)]
