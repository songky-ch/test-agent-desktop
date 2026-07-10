# 本地启动与调试手册

## 1. 环境准备

建议使用 Python 3.10 或 3.11。

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
```

如果要试 LangGraph 可选适配:

```bash
python -m pip install -e ".[p8]"
```

## 2. 启动 Desktop

```bash
python -m app.desktop
```

PyCharm 中可以创建 Python 运行配置:

- Module name: `app.desktop`
- Working directory: 项目根目录
- Python interpreter: 当前项目 `.venv`

## 3. 推荐试跑流程

1. 上传 `examples/requirements/online-education-requirement.md`。
2. 导入知识库 `examples/knowledge/defect-history.md` 和 `examples/knowledge/api-guidelines.md`。
3. 输入补充需求: `重点关注重复报名、课程下架、支付超时回调。`
4. 点击转换 Markdown。
5. 点击拆解测试点。
6. 编辑或确认测试点。
7. 点击生成测试用例。
8. 导出 Markdown 或 Excel。

默认会勾选“使用模型生成”。生成测试点和测试用例时会使用当前保存的 Ollama 或 OpenAI-compatible API 模型配置。补充需求输入框内容会作为 Prompt 的补充上下文传入模型。

## 4. Ollama 模式

Ollama 模型列表来自本机命令:

```bash
ollama list
```

Desktop 只展示本地已安装模型。没有安装 Ollama 或没有模型时, 下拉列表会为空。

## 5. OpenAI-compatible API 模式

API 模式需要配置:

- Base URL。
- API Key。
- Model Name。

Ollama 模式和 API 模式互斥, 切换来源后只保留当前模式需要的输入项。

默认安装包含 keyring。API Key 会优先写入系统密钥管理; 如果当前系统 keyring 不可用, 会回退写入本地配置文件, 保证本地调试不中断。

## 6. Windows 本地 Qdrant

当前方案不依赖 Docker。

1. 下载并解压 Windows 版 Qdrant。
2. 直接运行 `qdrant.exe`。
3. 保持默认 REST 地址 `http://localhost:6333`。
4. Desktop 中选择向量库 `Qdrant`。
5. Collection 默认使用 `test_agent_desktop`。
6. 勾选启用向量检索。

点击“测试 RAG”可以验证 Qdrant 和 Ollama embedding 是否可用。仅选择 Qdrant 不会写入向量; 需要在启用向量检索后添加知识库文档, 系统才会生成 embedding 并写入 Qdrant。

Embedding 默认使用 Ollama:

```bash
ollama pull nomic-embed-text
ollama serve
```

## 7. PyInstaller 打包

安装打包依赖:

```bash
python -m pip install -e ".[packaging]"
```

执行打包:

```bash
pyinstaller packaging/test-agent-desktop.spec --noconfirm
```

产物目录:

```text
dist/TestAgentDesktop/
```

当前 spec 会一起带上 `skills/`、`assets/`、`examples/`。
当前 spec 也会带上 `prompts/`, 保证打包后模型生成仍使用外置 Prompt。

## 8. 常见问题

### pip install -e . 提示发现多个顶层包

当前项目已在 `pyproject.toml` 限定 setuptools 只发现 `app*`, 正常不会再触发该问题。

### macOS 启动出现 IMKCFRunLoopWakeUpReliable 或 CapsLock 日志

这是 macOS 输入法和键盘状态框架日志, 不影响业务功能。

### Qdrant 连接失败

确认 `qdrant.exe` 已启动, 并且 Desktop 中 URL 是 `http://localhost:6333`。

### 向量检索没有结果

确认 Ollama embedding 模型已安装, Embedding 模型名与本地模型一致, 并适当降低相似度阈值。

### API 模型调用失败

确认 Base URL、API Key、Model Name 三项匹配同一个 OpenAI-compatible 服务。
