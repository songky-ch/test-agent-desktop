# P3-P7 后续开发计划

## P3: UI 完整联动

目标: 让已有后端能力能在 Desktop 中完整操作。

交付:

- 知识库导入按钮, 调用 `ApplicationService.import_knowledge_document`。
- RAG 统计实时刷新, 展示文档数、分块数、索引路径。
- 模型连接测试按钮, 分别测试 Ollama 和 OpenAI-compatible。
- 导出格式选择, 支持 Markdown 和 Excel。
- 测试用例表格编辑后同步回 `current_cases`。
- 生成后自动保存一次 ResultStore 运行记录。

验证:

- 服务层测试覆盖知识库导入、模型连接测试、导出格式、表格同步数据入口、运行记录保存。
- UI 编译检查通过。

## P4: 测试点确认与用例模板

目标: 满足 PRD 中“用户确认或编辑测试点”和“按用户模板生成测试用例”。

交付:

- 功能测试点结构化表格。
- 测试点编辑同步回 `current_points`。
- 默认用例模板对象 `CaseTemplate`。
- 用户可配置用例字段和输出顺序。
- 模型 Prompt 使用模板字段约束输出。

验证:

- 编辑测试点后生成用例使用最新数据。
- 自定义模板影响 Markdown / Excel 导出字段。

## P5: RAG 增强

目标: 从关键词检索升级到可替换向量检索架构。

交付:

- EmbeddingAdapter 接口。
- Ollama embedding 适配器。
- 本地向量索引适配器接口。
- Top-K 和相似度阈值真实生效。
- RAG 侧栏展示导入文档列表、分块数、索引状态。

验证:

- 导入知识库后可基于 query 召回相关分块。
- Top-K 和相似度阈值改变召回结果。

## P6: Skill 深度接入

目标: Skill 不只是后端加载, 而是成为用户可选能力。

交付:

- UI 展示已加载 Skills。
- 支持选择 Skill 并执行。
- 内置 `write_ppt`、`analyze_defects`、`api_test_design` 示例。
- Skill 执行结果进入 ResultStore。

验证:

- UI 能列出 Skill。
- 选中 Skill 后能调用对应 handler。
- Skill 错误能清晰展示。

## P7: 打包与本地运行体验

目标: 让项目具备可交付、可调试、可复现的本地运行形态。

交付:

- PyInstaller 配置。
- 示例需求文档。
- 示例知识库。
- 本地启动和调试手册。
- 常见问题排查: Ollama 未安装、API 连接失败、文档解析依赖缺失。

验证:

- 新环境按 README 可启动。
- 打包命令可生成本地应用包。
