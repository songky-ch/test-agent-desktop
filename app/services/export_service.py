from pathlib import Path

from app.models.entities import CaseTemplate, TestCase


CASE_FIELD_LABELS = {
    "case_id": "用例编号",
    "module": "所属模块",
    "function": "功能点",
    "precondition": "前置条件",
    "steps": "测试步骤",
    "expected_results": "预期结果",
    "priority": "优先级",
    "case_type": "类型",
    "remark": "备注",
}

CASE_FIELD_KEYS_BY_LABEL = {label: key for key, label in CASE_FIELD_LABELS.items()}


DEFAULT_CASE_TEMPLATE = CaseTemplate(
    fields=[
        "case_id",
        "module",
        "function",
        "precondition",
        "steps",
        "expected_results",
        "priority",
        "case_type",
        "remark",
    ]
)


def case_template_labels(template: CaseTemplate) -> list[str]:
    return [CASE_FIELD_LABELS[field] for field in template.fields]


class ExportService:
    def __init__(self, output_dir: Path):
        self.output_dir = Path(output_dir)

    def export_cases_markdown(
        self,
        cases: list[TestCase],
        filename: str = "test-cases.md",
        template: CaseTemplate = DEFAULT_CASE_TEMPLATE,
    ) -> Path:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        output = self.output_dir / filename
        labels = [CASE_FIELD_LABELS[field] for field in template.fields]
        rows = [
            "# 测试用例",
            "",
            "| " + " | ".join(labels) + " |",
            "| " + " | ".join(["---"] * len(labels)) + " |",
        ]
        for case in cases:
            rows.append("| " + " | ".join([self._case_value(case, field, "<br>") for field in template.fields]) + " |")
        output.write_text("\n".join(rows) + "\n", encoding="utf-8")
        return output

    def export_cases_excel(
        self,
        cases: list[TestCase],
        filename: str = "test-cases.xlsx",
        template: CaseTemplate = DEFAULT_CASE_TEMPLATE,
    ) -> Path:
        try:
            import openpyxl
        except ImportError as exc:
            raise RuntimeError("openpyxl is required to export .xlsx files") from exc

        self.output_dir.mkdir(parents=True, exist_ok=True)
        output = self.output_dir / filename
        workbook = openpyxl.Workbook()
        sheet = workbook.active
        sheet.title = "测试用例"
        sheet.append([CASE_FIELD_LABELS[field] for field in template.fields])
        for case in cases:
            sheet.append([self._case_value(case, field, "\n") for field in template.fields])
        workbook.save(output)
        return output

    def _case_value(self, case: TestCase, field: str, joiner: str) -> str:
        value = getattr(case, field)
        if isinstance(value, list):
            return joiner.join(value)
        return value
