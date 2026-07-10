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
- P3 UI 完整联动: 知识库导入、RAG 统计刷新、模型连接测试、Markdown/Excel 导出选择、结果持久化。
- P4 测试点确认与用例模板: 测试点结构化表格、中文模板字段、模板字段影响导出和模型 Prompt。
- P5 RAG 增强: Ollama embedding、本地 JSON 向量索引、Windows 本地 Qdrant REST 适配、Top-K 和相似度阈值。
- P6 Skill 深度接入: UI 展示、选择、执行 Skill, 内置用例生成、缺陷分析、接口测试设计。
- P7 本地运行体验: PyInstaller 打包配置、示例需求/知识库、本地调试手册、最终差距自检。
- P8 本地可用性完善: Prompt 文件化、API Key keyring 安全存储、Qdrant project_id 过滤、Skill 结构化错误、LangGraph 可选适配入口。

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

P0 到 P8 本地可用主链路已经闭合。下一步建议做目标系统实测: Windows Qdrant/Ollama、PyInstaller 打包产物、真实 API 模型调用。

## 开发约束

- 默认中文沟通。
- 精准修改, 不做无关优化。
- UI 不写业务逻辑, 只调用 ApplicationService。
- 新行为先用测试固定契约, 再实现。
- 开发过程记录到 `docs/development/development-log.md`。
