# Test Agent Desktop 开发记录

## 2026-07-09 阶段 1: 从 UI 壳子走向架构主干

### 目标

在已有 PySide6 壳子基础上补齐架构图里的主链路:

```text
Desktop UI -> Application Service -> Config / Document / Agent / RAG / Skill / Export
Document -> Markdown Store -> RAG -> Agent -> LLM Adapter -> Result Store -> UI
```

### 当前判断

已有代码能启动 UI, 也能用规则逻辑生成测试点和用例, 但还不是“完整 Agent 架构”:

- Agent 只是同步规则函数, 没有工作流状态。
- RAG 只是从知识库目录读 Markdown, 没有导入、切分、索引持久化。
- 模型配置已保存, 但旧实现把 Ollama 和 API Key/Base URL 混在同一组字段里。
- 生成结果只存在内存中, 没有 Result Store。
- Skill 能加载和调用, 但没有纳入主流程。

### 开发原则

- 严格沿 PRD 架构图补模块, 不把逻辑塞进 UI。
- 每个阶段至少有一条端到端可验证链路。
- LLM、LangGraph、向量库先做可替换接口, 本地仍可无外部服务运行。
- 所有新增行为先写测试, 再实现。
- 开发记录只沉淀关键判断、边界和验证结果, 不记录无意义流水账。

### 阶段 1 交付边界

- 新增互斥模型路由: Ollama 本地模型模式和 OpenAI-compatible API 模式解耦。
- 新增 Agent 工作流状态对象, 明确 `load -> retrieve -> generate_points -> generate_cases -> persist`。
- RAG 支持导入 Markdown 文档、切分、关键词索引持久化、Top-K 检索。
- Result Store 保存测试点和测试用例 JSON/Markdown 结果。
- ApplicationService 串联上述模块。

### 阶段 1 实际实现

- `app/agent/llm_provider.py`: 提供 ModelRouter、OllamaAdapter、OpenAI-compatible Chat Completions 调用适配器。
- `app/agent/workflow.py`: 用 `WorkflowState` 表达 Agent 编排状态, 当前节点顺序为 `retrieve_context -> generate_test_points -> generate_test_cases`。
- `app/rag/engine.py`: 支持导入 Markdown、切分段落、保存 `index.json`、按关键词 Top-K 检索。
- `app/services/result_store.py`: 保存一次生成运行的测试点和测试用例 JSON。
- `app/services/application_service.py`: 由直接调用规则 Agent 改为通过 `AgentWorkflow` 串联 RAG 和生成流程。

### 阶段 1 验证

```bash
.venv/bin/python -m unittest discover -s tests
```

结果: 12 个测试通过。

### 思考精华

- “严格遵守架构图”不等于立即绑定所有重型依赖。当前先把架构边界做实, 让 LLM、LangGraph、FAISS/Chroma 都有明确替换点。
- UI 不承载业务逻辑。Desktop 只触发 ApplicationService, 这样后续接 LangGraph 或真实向量库不需要重写 UI。
- RAG 一期优先保证可解释和本地可跑。关键词索引不是最终形态, 但它已经具备导入、切分、持久化、召回这四个稳定接口。
- Agent Workflow 先用轻量状态机表达节点顺序。后续换成 LangGraph 时, 节点输入输出已经固定, 风险会小很多。

## 2026-07-09 阶段 1.1: 解耦 Ollama 和 API Key 配置

### 文档变化

新版 PRD 明确模型来源是两种互斥模式:

- Ollama 本地模型模式: 不配置 API Key, 不配置 Base URL, 从 `ollama list` 选择本地模型。
- OpenAI-compatible API 模式: 配置 Base URL、API Key、Model Name。

### 修改内容

- `ModelConfig` 改为 `source + ollama_model + api_base_url + api_key + api_model`。
- 保留旧配置读取兼容, 旧的 `provider/use_ollama/base_url/model` 会自动归一成新结构。
- `llm_provider.py` 新增 `ModelRouter` 和 `OllamaAdapter`。
- PySide6 模型配置 UI 按来源切换字段: Ollama 模式只展示本地模型; API 模式才展示 Base URL、Model、API Key。

### 思考精华

- API Key 不是“模型配置”的通用字段, 它只属于 OpenAI-compatible API 模式。
- Ollama 的 Base URL 可以作为内部调用细节, 但不应该暴露给用户作为必填配置。
- UI 必须体现互斥关系, 否则用户会误以为两套配置能同时生效。

## 2026-07-09 阶段 2: 真实模型生成链路

### 目标

让 Agent 不再只能依赖规则生成, 而是在用户启用模型时通过 ModelRouter 调用 Ollama 或 OpenAI-compatible 模型, 并把模型 JSON 输出解析为现有 `TestPoint` 和 `TestCase`。

### 修改内容

- `app/agent/model_generation.py`: 新增 `ModelGenerationService`, 构造测试 Agent Prompt, 调用模型路由, 解析 JSON。
- `app/agent/workflow.py`: 支持可选模型生成节点 `generate_with_model`; 未启用模型时仍走规则 fallback。
- `app/services/application_service.py`: `generate_test_points` 增加 `use_model` 参数, 根据当前 `ModelConfig` 创建 `ModelRouter`。
- `app/desktop/main_window.py`: 操作区增加“使用模型生成”开关。
- `tests/test_model_generation.py`: 覆盖模型 JSON 解析和坏 JSON 错误。
- `tests/test_application_model_generation.py`: 覆盖 ApplicationService 真实模型生成分支。

### 设计判断

- 模型输出只接受 JSON, 不接受 Markdown 表格或解释文本, 这样后续 UI 和导出层不用猜格式。
- 规则生成保留为 fallback, 便于用户无本地模型或无 API Key 时仍能启动和体验主流程。
- `ModelGenerationService` 不知道具体模型来源, 只依赖 `ModelRouter.chat`, 保持 Ollama/API 解耦。
- Workflow 的节点记录保留, 便于后续调试和展示 Agent 执行轨迹。

### 验证

```bash
.venv/bin/python -m unittest discover -s tests
PYTHONPYCACHEPREFIX=/private/tmp/test-agent-pycache .venv/bin/python -m compileall app
```

结果: 16 个测试通过, 编译检查通过。

## 2026-07-09 阶段 2.1: 文档列表移除与 Ollama 模型来源确认

### 问题确认

- 文档上传列表只有选择入口, 没有移除入口。用户修改需求文档时无法把旧文件从当前任务列表中拿掉。
- Ollama 模型列表已不是写死值。当前实现路径是 `MainWindow._refresh_ollama_models -> ApplicationService.list_ollama_models -> OllamaAdapter.list_models -> subprocess.run(["ollama", "list"])`。

### 修改内容

- `app/desktop/main_window.py`: 文档上传区新增“移除选中文档”按钮。
- 移除操作只删除 UI 列表项, 不删除磁盘原始文件。
- 开发文档记录 Ollama 模型列表来源, 便于后续排查本地模型展示问题。

### 设计判断

- “移除选中文档”是当前任务列表管理动作, 不是文件系统删除动作, 避免误删用户原始需求文档。
- Ollama 模型列表依赖本机 `ollama` CLI; 如果本地未安装 Ollama 或命令失败, 当前实现返回空列表, UI 不崩溃。

## 2026-07-09 阶段 3: UI 完整联动

### 目标

把已有服务层能力接到 Desktop UI, 让用户可以在界面上完成知识库导入、模型连接测试、格式化导出、编辑后同步和结果持久化。

### 修改内容

- `app/services/application_service.py`: 新增 `test_model_connection`、`export_cases`、`sync_cases_from_rows`、`rag_stats`。
- `app/models/entities.py`: 新增 `ConnectionTestResult`。
- `app/desktop/main_window.py`: 新增知识库导入按钮、RAG 文档列表、RAG 统计刷新、模型连接测试按钮、导出格式选择、表格编辑同步。
- `tests/test_p3_application_ui_support.py`: 覆盖 P3 服务层契约。

### 设计判断

- UI 的表格编辑不直接改实体对象, 而是在导出前统一通过 `sync_cases_from_rows` 同步, 避免每次单元格变化都写业务逻辑。
- 导出统一走 `ApplicationService.export_cases(format)`, UI 不直接知道 Markdown/Excel 细节。
- 模型连接测试复用当前保存的 `ModelConfig`, 保证测试对象和后续生成对象一致。
- RAG 侧栏先展示文档列表和索引统计, Top-K 和相似度阈值留给 P5 做真实检索增强。

### 验证

```bash
.venv/bin/python -m unittest discover -s tests
PYTHONPYCACHEPREFIX=/private/tmp/test-agent-pycache .venv/bin/python -m compileall app
```

结果: 20 个测试通过, 编译检查通过。

## 2026-07-09 阶段 4: 测试点确认与用例模板

### 目标

让用户能在生成后确认或编辑测试点, 并用自定义字段顺序控制测试用例导出和模型输出约束。

### 修改内容

- `app/models/entities.py`: 新增 `CaseTemplate`。
- `app/services/export_service.py`: Markdown / Excel 导出支持按模板字段和顺序输出。
- `app/services/application_service.py`: 新增 `sync_points_from_rows` 和 `save_case_template`。
- `app/agent/model_generation.py`: Prompt 增加当前用户用例模板字段顺序。
- `app/desktop/main_window.py`: 功能测试点 Tab 改为可编辑表格; 操作区新增模板字段输入框。
- `tests/test_p4_case_template.py`: 覆盖编辑测试点后生成用例、模板导出、Prompt 模板字段约束。

### 设计判断

- P4 首版使用逗号分隔字段列表配置模板, 不做多模板管理和拖拽排序。
- 测试点表格编辑后, 在生成用例前统一同步回 `current_points`, 避免 UI 单元格事件直接写业务逻辑。
- 导出字段顺序由 `CaseTemplate.fields` 决定, 默认字段保持 PRD 默认用例字段。
- 模型 Prompt 使用同一份模板字段, 确保模型生成和导出层对字段约束一致。

### 验证

```bash
.venv/bin/python -m unittest discover -s tests
PYTHONPYCACHEPREFIX=/private/tmp/test-agent-pycache .venv/bin/python -m compileall app
```

结果: 23 个测试通过, 编译检查通过。

## 2026-07-09 阶段 4.1: 模板字段中文化与 macOS 启动日志确认

### 问题确认

- 模板字段输入框显示 `case_id,module,function...`, 对用户来说是内部字段名, 不符合中文产品体验。
- macOS 启动时出现 `IMKCFRunLoopWakeUpReliable` 和 `TSM AdjustCapsLockLEDForKeyTransitionHandling` 日志。

### 修改内容

- 用例模板输入统一改为中文字段: `用例编号,所属模块,功能点,前置条件,测试步骤,预期结果,优先级,类型,备注`。
- 服务层支持中文字段映射到内部字段 key。
- 模型 Prompt 中展示中文模板字段顺序。

### 日志判断

上述两条日志来自 macOS 输入法/键盘状态框架, 常见于 Python + Qt/PySide 桌面应用启动或输入控件聚焦时。

当前判断:

- 不影响业务功能。
- 不影响模型调用、文档解析、RAG、导出。
- 不建议通过重定向 stderr 在应用内消音, 这会掩盖真正的错误日志。

## 2026-07-09 阶段 5: RAG 向量检索增强

### 目标

把关键词 RAG 升级为可选向量检索, 让 Top-K、相似度阈值和 Embedding 模型真实参与召回。

### 实现方案

- 支持本地 JSON 向量索引: `data/knowledge/vector_index.json`。
- 支持 Windows 本地 Qdrant: 默认 `http://localhost:6333`, Collection `test_agent_desktop`。
- Embedding 默认走 Ollama: `http://localhost:11434/api/embeddings`。
- 如果未启用向量检索, 或 embedding 不可用, 仍保留关键词 fallback。

### 本地准备

如果要体验向量检索:

```bash
ollama pull nomic-embed-text
ollama serve
```

然后在 UI 中:

- 向量库可选择 `本地 JSON` 或 `Qdrant`。
- 使用 Qdrant 时, Windows 直接运行本地 `qdrant.exe`, 默认 REST 地址为 `http://localhost:6333`。
- 勾选“启用向量检索”。
- Embedding 模型填写 `nomic-embed-text`。
- Top-K 例如 `5`。
- 相似度阈值例如 `0.30`。

### 修改内容

- `app/rag/embeddings.py`: 新增 `EmbeddingAdapter` 和 `OllamaEmbeddingAdapter`。
- `app/rag/vector_index.py`: 新增本地 JSON 向量索引。
- `app/rag/qdrant_index.py`: 新增 Qdrant REST 向量索引。
- `app/rag/engine.py`: 支持向量索引写入、向量召回、Top-K、相似度阈值。
- `app/services/application_service.py`: 新增 `configure_rag`。
- `app/desktop/main_window.py`: RAG 侧栏新增向量库选择、启用向量检索、Top-K、相似度阈值、Embedding 模型、Qdrant URL 和 Collection 输入。
- `tests/test_p5_vector_rag.py`: 覆盖向量召回、阈值过滤、服务层参数配置。
- `tests/test_p5_qdrant_vector_index.py`: 覆盖 Qdrant Collection 创建、Upsert、Search。

### 设计判断

- P5 支持本地 JSON 和 Qdrant 两种模式, 既能零依赖体验, 也能贴近 Windows 本地向量数据库部署。
- `RagEngine` 只依赖 `EmbeddingAdapter` 和向量索引接口, 后续替换 FAISS/Chroma 或扩展 Qdrant payload 不需要改 UI 和 Agent。
- 单元测试使用 FakeEmbeddingAdapter, 不依赖本地 Ollama, 保证测试稳定。

### 验证

```bash
.venv/bin/python -m unittest discover -s tests
PYTHONPYCACHEPREFIX=/private/tmp/test-agent-pycache .venv/bin/python -m compileall app
```

结果: 28 个测试通过, 编译检查通过。

## 2026-07-10 阶段 6: Skill 深度接入

### 目标

让 Skill 不只存在于后端加载机制中, 而是能在 Desktop UI 中展示、选择、执行, 并把执行结果落到本地结果目录。

### 修改内容

- `app/services/application_service.py`: 新增 `list_skills` 和 `run_skill`, Skill 执行结果保存到 `data/outputs/skills/<skill>.json`。
- `app/desktop/main_window.py`: 新增 Skill 下拉、刷新按钮、执行按钮和结果预览。
- `skills/analyze_defects`: 新增缺陷分析示例 Skill。
- `skills/api_test_design`: 新增接口测试设计示例 Skill。
- `tests/test_p6_skill_integration.py`: 覆盖 Skill 列表、执行和结果保存。

### 设计判断

- 保留现有目录式 Skill 协议: `skill.yaml + prompt.md + handler.py`。
- P6 首版不做插件市场和权限管理。
- UI 执行 Skill 使用当前补充说明、测试点、用例组装 payload, 保持 Skill 与主流程数据打通。

### 验证

```bash
.venv/bin/python -m unittest discover -s tests
PYTHONPYCACHEPREFIX=/private/tmp/test-agent-pycache .venv/bin/python -m compileall app skills
```

结果: 29 个测试通过, 编译检查通过。

### 暂不进入

- 企业账号、多人协作、权限系统。
- 自动执行测试。
- 插件市场。
- FAISS/Chroma 后续作为 `RagEngine` 的可选替换实现接入。

## 2026-07-10 阶段 7: 打包与本地运行体验

### 目标

补齐一期最后的本地交付体验, 让项目不仅能开发运行, 也能被用户按手册试跑、导入样例、执行打包, 并明确当前代码和 PRD 之间的剩余差距。

### 修改内容

- `packaging/test-agent-desktop.spec`: 新增 PyInstaller 打包配置, 打包时带上 `skills/`、`assets/`、`examples/`。
- `examples/requirements/online-education-requirement.md`: 新增可直接上传的需求样例。
- `examples/knowledge/defect-history.md`: 新增历史缺陷知识库样例。
- `examples/knowledge/api-guidelines.md`: 新增接口测试规范知识库样例。
- `docs/development/local-debug-guide.md`: 新增本地启动、PyCharm 调试、Ollama、API、Qdrant、打包和常见问题手册。
- `docs/development/final-gap-check.md`: 新增 PRD 与代码最终差距自检。
- `pyproject.toml`: 新增 `packaging` 可选依赖, 用于安装 PyInstaller。

### 设计判断

- PyInstaller 作为可选依赖, 不进入默认安装链路, 避免影响日常开发启动。
- 示例资料选择在线教育报名场景, 因为它同时覆盖登录、权限、重复提交、库存、支付、订单状态、移动端兼容等典型测试点。
- P7 不把未验证的打包产物描述为已验证安装包, 只交付可执行 spec 和本地打包手册。

### 最终自检结论

一期主链路已经闭合:

```text
文档上传 -> Markdown -> 补充需求 -> RAG -> 测试点 -> 用例 -> Skill -> 导出 -> 打包配置
```

仍建议后续进入 P8 的内容:

- 目标 Windows/macOS 打包产物实测。
- LangGraph 真实依赖接入。
- Qdrant payload 过滤。
- Skill 结构化错误展示。
- 模型 Prompt 文件化。
- API Key 安全存储。

## 2026-07-10 阶段 8: 本地可用性完善

### 目标

沿 P7 自检方向继续补齐本地可直接使用时最容易卡住的点: 配置安全、Prompt 可维护、RAG 项目隔离、Skill 错误可读、LangGraph 后续接入入口。

### 修改内容

- `prompts/model_generation.md`: 模型生成 Prompt 从代码中外置。
- `ModelGenerationService`: 支持读取外置 Prompt, 并注入中文用例模板字段。
- `ConfigManager`: API Key 优先写入系统 keyring, keyring 不可用时回退本地配置文件。
- `QdrantVectorIndex`: payload 增加 `project_id`, search 请求增加 project filter。
- `ApplicationService.configure_rag`: 支持传入 `project_id`。
- `SkillRuntime`: Skill 执行统一返回 `ok/result/error_type/message` 结构。
- `MainWindow`: Skill 输出改为格式化 JSON, 失败时展示失败信息。
- `LangGraphAgentWorkflow`: 新增可选 LangGraph 适配入口。
- `pyproject.toml`: 默认依赖加入 keyring, `p8` 可选依赖加入 LangGraph。

### 设计判断

- API Key 安全存储不能成为本地启动阻塞点, 所以 keyring 失败时允许回退。
- Qdrant 过滤使用 `project_id`, 先解决多项目共用 collection 的召回污染问题。
- LangGraph 作为可选适配入口存在, UI 默认仍走稳定状态机, 避免用户未安装可选依赖时启动失败。

### 验证

```bash
.venv/bin/python -m unittest discover -s tests
PYTHONPYCACHEPREFIX=/private/tmp/test-agent-pycache .venv/bin/python -m compileall app skills
```

结果: 31 个测试通过, 编译检查通过。

## 2026-07-10 阶段 8.1: Windows 本地验证问题修复

### 问题确认

- RAG 知识库文档只能添加, 不能删除。
- 用户直接点击生成测试点或测试用例时, 缺少当前 Markdown 校验和清晰提示。
- 规则 fallback 生成过弱, 容易让用户误以为没有使用当前需求文档。
- Qdrant 只配置后端, 缺少连接测试、向量数量和写入状态提示。
- Skill 缺少扩展说明。

### 修改内容

- RAG 支持移除知识库文档, 同步更新关键词索引和本地向量索引; Qdrant 支持按 `project_id + document` 删除向量。
- UI 新增“移除选中文档”和“测试 RAG”。
- RAG 统计新增向量数量展示。
- 生成测试点前强制要求已转换 Markdown。
- “使用模型生成”默认勾选, 生成前保存当前 Ollama/API 配置。
- 直接点击生成测试用例时, 如果还没有测试点, 会先基于当前文档生成测试点。
- 规则 fallback 改为按当前文档正文拆多个测试点。
- 新增 `docs/development/skill-extension-guide.md` 说明 Skill 的作用、输入和扩展方式。

### 验证

```bash
.venv/bin/python -m unittest discover -s tests
PYTHONPYCACHEPREFIX=/private/tmp/test-agent-pycache .venv/bin/python -m compileall app skills
```

结果: 37 个测试通过, 编译检查通过。

## 2026-07-10 阶段 8.2: Ollama / Qdrant Windows 错误提示修复

### 问题确认

- 添加 RAG 文档时报 `model nomic-embed-text not found`, 根因是本机 Ollama 未安装 embedding 模型。
- 拆解测试点时报 HTTP 404, 常见原因是把 embedding 模型选成了主生成模型, 或本地 Ollama 生成模型未安装。
- Qdrant collection 未创建时, 统计接口可能返回 404, 不应直接打断 UI。

### 修改内容

- `OllamaEmbeddingAdapter` 兼容 `/api/embed` 和旧版 `/api/embeddings`。
- embedding 模型不可用时, 明确提示执行 `ollama pull <model>`。
- 主生成模型如果选择了 embedding 模型, 直接提示用户改选对话模型。
- Qdrant 统计遇到 collection 404 时返回 0, 不再中断 UI。
- RAG 导入和删除增加 UI 异常提示。

### 本地配置要求

Ollama 至少需要两类模型:

```bash
ollama pull qwen2.5:7b
ollama pull nomic-embed-text
```

- `qwen2.5:7b` 这类对话模型用于生成测试点和测试用例。
- `nomic-embed-text` 用于 RAG 向量化。

### 验证

```bash
.venv/bin/python -m unittest discover -s tests
PYTHONPYCACHEPREFIX=/private/tmp/test-agent-pycache .venv/bin/python -m compileall app skills
```

结果: 41 个测试通过, 编译检查通过。
