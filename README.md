# Test Agent Desktop

面向测试人员的本地 Desktop AI Agent, 用于把需求文档转换为 Markdown, 拆解功能测试点, 生成测试用例, 并导出 Markdown/Excel。

## 当前实现

- PySide6 Desktop UI 骨架。
- Application Service 串联文档、Agent、RAG、Skill、导出。
- 支持 `.txt`、`.md`、`.docx`、`.pdf`、`.xlsx` 转 Markdown。
- 本地规则版测试点和测试用例生成。
- 本地关键词 RAG 占位实现。
- 目录式 Skill 加载和调用机制。
- Markdown 导出和 Excel 导出服务。
- 模型路由层: Ollama 本地模型和 OpenAI-compatible API 模型互斥选择。
- Ollama 适配层: 从 `ollama list` 读取本地模型, 不配置 API Key/Base URL。
- OpenAI-compatible 适配层: 仅 API 模式配置 Base URL、API Key、Model。
- Agent Workflow 状态编排。
- 可选真实模型生成: 启用后通过 ModelRouter 调用模型并解析 JSON。
- Result Store 运行结果持久化。
- UI 完整联动: 知识库导入、RAG 统计刷新、模型连接测试、Markdown/Excel 导出选择。
- 测试点确认与用例模板: 结构化测试点表格、模板字段导出、模型 Prompt 字段约束。
- RAG 增强: Ollama embedding、本地 JSON 向量索引、Qdrant、Top-K 和相似度阈值。
- Windows Qdrant: 直接运行本地 `qdrant.exe`, 默认连接 `http://localhost:6333`。
- Skill 深度接入: UI 展示并执行 Skill, 内置用例生成、缺陷分析、接口测试设计示例。
- P7 本地运行体验: PyInstaller 打包配置、示例需求/知识库、本地启动与调试手册、最终差距自检。
- P8 本地可用性完善: Prompt 文件化、API Key keyring 安全存储、Qdrant 项目级过滤、Skill 结构化错误、LangGraph 可选适配入口。

## 开发文档

- [开发记录](docs/development/development-log.md)
- [架构开发路线](docs/development/architecture-roadmap.md)
- [本地启动与调试手册](docs/development/local-debug-guide.md)
- [P7 最终差距自检](docs/development/final-gap-check.md)
- [Skill 扩展说明](docs/development/skill-extension-guide.md)

## 本地启动

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
python -m app.desktop
```

## 验证

```bash
python3 -m unittest discover -s tests
python3 -m compileall app
```

当前测试数: 37。

## P8 可选依赖

默认安装已包含 keyring, API Key 会优先写入系统密钥管理。LangGraph 作为可选依赖安装:

```bash
python -m pip install -e ".[p8]"
```

## 打包

```bash
python -m pip install -e ".[packaging]"
pyinstaller packaging/test-agent-desktop.spec --noconfirm
```

产物目录: `dist/TestAgentDesktop/`。

## 示例资料

- 示例需求: `examples/requirements/online-education-requirement.md`
- 示例知识库: `examples/knowledge/defect-history.md`
- 接口测试规范: `examples/knowledge/api-guidelines.md`

## 目录

```text
app/
  desktop/
  services/
  agent/
  documents/
  rag/
  skills/
  models/
  config/
data/
  projects/
  markdown/
  indexes/
  outputs/
skills/
  generate_test_cases/
  analyze_defects/
  api_test_design/
examples/
  requirements/
  knowledge/
packaging/
prompts/
tests/
```
