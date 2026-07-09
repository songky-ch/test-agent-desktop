def run(payload):
    points = payload.get("points", [])
    cases = []
    for index, point in enumerate(points, start=1):
        cases.append(
            {
                "case_id": f"TC-{index:03d}",
                "module": point.get("module", "默认模块"),
                "function": point.get("function", "需求功能"),
                "priority": point.get("priority", "P1"),
            }
        )
    return {"cases": cases}
