# 压缩上下文

## 项目目标

Test Agent Desktop 是面向测试人员的本地 Desktop AI Agent。核心链路是: 上传需求文档 -> 转 Markdown -> 补充需求 -> 可选 RAG -> 拆解功能测试点 -> 生成测试用例 -> 导出 Markdown/Excel。

## 已确认架构

项目严格沿 PRD 架构图拆分:

```text
Desktop UI -> ApplicationService
ApplicationService -> Config / Document / Agent / RAG / Skill / Export
Document -> Markdown Store -> RAG -> Agent -> Model Router -> Result Store -> UI
```

## 已完成

- PySide6 UI 壳子和主操作区。
- 文档转 Markdown 管线。
- 规则版 Agent Orchestrator。
- AgentWorkflow 状态编排。
- RAG Markdown 导入、切分、关键词索引、Top-K 检索。
- SkillRuntime 目录式加载。
- ResultStore JSON 持久化。
- Markdown/Excel 导出服务。
- `pip install -e .` 包发现问题已修复。

## 最新 PRD 变化

模型配置已解耦为两种互斥来源:

- Ollama 本地模型模式: 不配置 API Key, 不配置 Base URL, 从 `ollama list` 选择本地模型。
- OpenAI-compatible API 模式: 配置 Base URL、API Key、Model Name。

当前代码已按此修改:

- `ModelConfig`: `source + ollama_model + api_base_url + api_key + api_model`。
- `ModelRouter`: 互斥选择 OllamaAdapter 或 OpenAiCompatibleProvider。
- UI: 按模型来源切换字段。
- Ollama 模型下拉不是写死数据, 来源是本地 `ollama list`。
- 文档上传列表支持移除选中文档, 但不删除磁盘原文件。

## 当前下一阶段

进入 P2: 真实 Agent 生成链路。

目标:

- 增加 Prompt 模板。
- 用 ModelRouter 调用真实模型。
- 解析模型输出 JSON。
- 失败时返回清晰错误, 不静默吞掉。
- 保留规则生成作为无模型配置时的本地可运行路径。

## 开发约束

- 默认中文沟通。
- 精准修改, 不做无关优化。
- UI 不写业务逻辑, 只调用 ApplicationService。
- 新行为先用测试固定契约, 再实现。
- 开发过程记录到 `docs/development/development-log.md`。
