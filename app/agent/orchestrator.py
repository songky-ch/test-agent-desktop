from app.models.entities import RequirementContext, TestCase, TestPoint


class AgentOrchestrator:
    def generate_test_points(self, context: RequirementContext) -> list[TestPoint]:
        lines = self._body_lines(context.markdown)
        module = self._first_heading(context.markdown)
        functions = lines[:8] or [self._first_body_line(context.markdown)]
        source_text = context.markdown + "\n" + context.supplemental
        data_checks = self._matching_lines("\n".join(context.rag_context) + "\n" + source_text, ["缺陷", "校验", "重复", "必填"])

        points = []
        for function in functions:
            points.append(
                TestPoint(
                    module=module,
                    function=function,
                    positive_scenarios=[f"验证{function}主流程可按当前需求完成"],
                    negative_scenarios=self._matching_lines(function + "\n" + source_text, ["错误", "失败", "异常", "不允许", "禁止"]),
                    boundary_scenarios=self._matching_lines(function + "\n" + source_text, ["边界", "小于", "大于", "最大", "最小", "为空"]),
                    exception_scenarios=self._matching_lines(function + "\n" + source_text, ["异常", "超时", "失败"]),
                    data_checks=data_checks,
                    permission_checks=self._matching_lines(function + "\n" + source_text, ["权限", "角色", "未登录"]),
                    compatibility_notes=self._matching_lines(context.supplemental, ["兼容", "Chrome", "Edge", "Firefox", "移动端"]),
                )
            )
        return points

    def generate_test_cases(self, points: list[TestPoint]) -> list[TestCase]:
        cases = []
        for index, point in enumerate(points, start=1):
            cases.append(
                TestCase(
                    case_id=f"TC-{index:03d}",
                    module=point.module,
                    function=point.function,
                    precondition="满足功能前置条件",
                    steps=[f"进入{point.module}模块", f"执行{point.function}", "观察页面和数据结果"],
                    expected_results=[f"{point.function}按需求完成"],
                    priority="P1",
                    case_type="正向",
                    remark="; ".join(point.negative_scenarios + point.data_checks),
                )
            )
        return cases

    def _first_heading(self, markdown: str) -> str:
        headings = []
        for line in markdown.splitlines():
            stripped = line.strip()
            if stripped.startswith("#"):
                headings.append(stripped.lstrip("#").strip())
        if len(headings) > 1:
            return headings[1]
        return headings[0] if headings else "默认模块"

    def _first_body_line(self, markdown: str) -> str:
        for line in markdown.splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                return stripped
        return "需求功能"

    def _body_lines(self, markdown: str) -> list[str]:
        lines = []
        for raw_line in markdown.splitlines():
            stripped = raw_line.strip().strip("-").strip()
            if not stripped or stripped.startswith("#"):
                continue
            lines.append(stripped)
        return lines

    def _matching_lines(self, text: str, keywords: list[str]) -> list[str]:
        matches = []
        for raw_line in text.replace(",", "\n").replace("，", "\n").splitlines():
            line = raw_line.strip()
            if line and any(keyword in line for keyword in keywords):
                matches.append(line.split(":", 1)[-1].strip())
        return matches
