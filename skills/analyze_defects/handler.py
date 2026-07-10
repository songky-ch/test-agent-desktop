def run(payload):
    items = payload.get("items", [])
    modules = {}
    for item in items:
        module = item.get("module", "未分类") if isinstance(item, dict) else "未分类"
        modules[module] = modules.get(module, 0) + 1
    return {
        "summary": f"共分析 {len(items)} 条缺陷记录",
        "hot_modules": modules,
        "retest_focus": ["高频模块回归", "严重缺陷复测", "关联流程冒烟"],
    }
