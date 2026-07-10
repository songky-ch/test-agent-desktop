# Skill 扩展说明

## 1. Skill 是什么

Skill 是主流程之外的可扩展能力。主流程负责:

```text
需求文档 -> Markdown -> 测试点 -> 测试用例 -> 导出
```

Skill 用来复用当前上下文做额外任务, 例如:

- 分析当前缺陷记录。
- 基于当前测试点生成接口测试清单。
- 基于当前用例生成评审摘要。

## 2. 当前 Skill 输入

点击“执行 Skill”时, Desktop 会把当前页面上下文传给 Skill:

```json
{
  "supplemental": "用户补充说明",
  "points": [{"module": "模块", "function": "功能点"}],
  "cases": [{"case_id": "TC-001", "module": "模块", "function": "功能点"}],
  "items": [{"module": "模块", "title": "功能点", "priority": "P1"}]
}
```

## 3. 新增 Skill

在 `skills/` 下创建目录:

```text
skills/my_skill/
  skill.yaml
  prompt.md
  handler.py
```

`skill.yaml`:

```yaml
name: my_skill
description: 我的扩展能力
entry: handler.py
```

`handler.py`:

```python
def run(payload):
    points = payload.get("points", [])
    return {
        "summary": f"收到 {len(points)} 个测试点",
        "items": points,
    }
```

返回值必须是可 JSON 序列化的数据。

## 4. 执行结果

系统会统一包装 Skill 结果:

```json
{
  "ok": true,
  "skill": "my_skill",
  "result": {}
}
```

如果执行失败:

```json
{
  "ok": false,
  "skill": "my_skill",
  "error_type": "ValueError",
  "message": "错误信息"
}
```
