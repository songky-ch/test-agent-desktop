# P7 最终差距自检

## 1. 对照 PRD 的完成情况

| PRD 能力 | 当前状态 | 说明 |
|---|---|---|
| 上传非固定格式需求文档 | 已完成 | 支持 `.docx`、`.pdf`、`.md`、`.txt`、`.xlsx`。 |
| 统一转换 Markdown | 已完成 | 文档进入 Agent 前先标准化为 Markdown。 |
| 补充需求输入 | 已完成 | UI 补充说明会进入测试点生成上下文。 |
| 功能测试点拆解 | 已完成 | 支持规则生成和可选模型生成。 |
| 测试点确认/编辑 | 已完成 | UI 表格可编辑并同步回服务层。 |
| 按模板生成测试用例 | 已完成 | 中文字段模板影响模型 Prompt 和导出。 |
| Ollama 本地模型 | 已完成 | 通过 `ollama list` 读取本地模型。 |
| OpenAI-compatible API | 已完成 | API 模式独立配置 Base URL、API Key、Model。 |
| 本地 RAG | 已完成 | 支持关键词、本地 JSON 向量索引、Windows 本地 Qdrant。 |
| Skill 扩展 | 已完成 | 支持目录式加载、UI 选择执行、结果保存。 |
| Markdown / Excel 导出 | 已完成 | 用例结果可导出两种格式。 |
| 本地打包 | 已完成第一版 | 已提供 PyInstaller spec, 需在目标 Windows/macOS 机器实测产物。 |
| Prompt 文件化 | 已完成 | 模型生成 Prompt 已移到 `prompts/model_generation.md`。 |
| API Key 安全存储 | 已完成第一版 | 优先写入 keyring, 不可用时回退本地配置文件。 |
| Skill 错误展示 | 已完成 | 统一返回结构化执行结果。 |

## 2. 架构一致性检查

当前代码保持以下边界:

```text
Desktop UI -> ApplicationService
ApplicationService -> Config / Document / Agent / RAG / Skill / Export
Document -> Markdown Store -> RAG -> Agent -> Model Router -> Result Store -> UI
```

检查结果:

- UI 只负责采集输入、展示状态和调用服务层。
- 文档解析集中在 `app/documents`。
- Agent 编排集中在 `app/agent`。
- RAG 能力集中在 `app/rag`。
- Skill 加载与执行集中在 `app/skills` 和 `skills/`。
- 导出集中在 `app/services/export_service.py`。
- 模型来源通过 `ModelRouter` 互斥选择。

## 3. 已知未进入一期的内容

以下内容属于 PRD 明确的非一期目标或后续增强:

- 多人协作。
- 云端账号体系。
- 在线数据库服务。
- 企业权限管理。
- 自动执行测试。
- 插件市场。
- 多模板管理和拖拽排序。

## 4. 需要后续完善的工程点

这些点不阻塞 P7 本地验证, 但建议作为下一轮迭代入口:

| 项目 | 当前状态 | 建议进入阶段 |
|---|---|---|
| Windows/macOS 打包实测 | 已提供 PyInstaller spec, 当前未在目标系统验证 | P9 |
| LangGraph UI 开关 | 已提供可选适配入口, UI 仍默认使用稳定状态机 | P9 |
| Qdrant Collection 清理 | 当前支持项目级过滤, 未提供 UI 清空 collection | P9 |
| 多模板管理 | 当前支持单模板字段顺序 | P9 |

## 5. 本阶段结论

P0 到 P7 的一期主链路已经闭合:

```text
文档上传 -> Markdown -> 补充需求 -> RAG -> 测试点 -> 用例 -> Skill -> 导出 -> 打包配置
```

下一步应优先做目标系统实测, 尤其是 Windows 下的 Qdrant、Ollama、PyInstaller 产物。
