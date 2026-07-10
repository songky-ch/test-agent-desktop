# 架构开发路线

## P0 已完成: 本地可启动壳子

- PySide6 主窗口。
- 文档上传入口。
- 模型配置表单。
- Markdown / 测试点 / 测试用例输出 Tab。
- RAG 侧栏静态展示。

## P1 当前: 架构主干

- Model Router。
- Ollama Adapter。
- OpenAI-compatible Adapter。
- Agent Workflow State。
- RAG 导入、切分、索引、检索。
- Result Store。
- ApplicationService 编排。

状态: 已完成第一版, 通过 12 个单元测试。

## P2 下一步: 真实 Agent 生成

- Prompt 模板管理。
- OpenAI-compatible Chat Completions 调用。
- JSON 输出解析。
- 失败时清晰展示错误, 不静默吞掉。

状态: 已完成第一版。Prompt 目前在 `ModelGenerationService` 中内置, 后续可独立为模板文件。

## P3 下一步: UI 完整联动

- 知识库文档导入按钮。
- RAG 统计实时刷新。
- 模型连接测试。
- 结果导出格式选择。

状态: 已完成第一版。Top-K、相似度阈值和 Embedding 模型的真实联动放入 P5。

## P4 已完成: 测试点确认与用例模板

- 功能测试点结构化表格。
- 测试点编辑同步回 `current_points`。
- `CaseTemplate` 支持字段和顺序。
- Markdown / Excel 导出按模板字段输出。
- 模型 Prompt 使用模板字段约束。

状态: 已完成第一版。多模板管理和拖拽排序不在当前范围。

## P5 已完成: RAG 增强

- EmbeddingAdapter 接口。
- Ollama embedding 适配器。
- 本地向量索引适配器接口。
- Qdrant 本地向量数据库适配。
- Top-K 和相似度阈值真实生效。
- RAG 侧栏展示导入文档列表、分块数、索引状态。

状态: 已完成第一版。支持本地 JSON 向量索引和 Windows 本地 Qdrant。

## P6 已完成: Skill 深度接入

- UI 展示已加载 Skill。
- 允许用户选择 Skill 生成结果。
- 内置 `generate_test_cases`, `analyze_defects`, `api_test_design`。

状态: 已完成第一版。插件市场和权限管理不在当前范围。

## P7 已完成: 打包与本地运行体验

- PyInstaller 配置。
- 示例需求文档。
- 示例知识库。
- 本地启动和调试手册。

状态: 已完成第一版。目标系统打包实测和安装包形态优化放入 P8。

## P8 已完成: 本地可用性完善

- 模型生成 Prompt 文件化。
- API Key 优先写入系统 keyring, 不可用时回退到本地配置文件。
- Qdrant 向量召回增加 `project_id` payload 过滤。
- Skill 执行结果统一为 `ok/result/error_type/message` 结构。
- UI 格式化展示 Skill JSON 结果。
- LangGraph 增加可选适配入口。

状态: 已完成第一版。Windows/macOS 打包产物仍需在目标系统实测。
