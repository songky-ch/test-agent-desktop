# P5 RAG 增强实现方案

## 目标

把当前关键词 RAG 升级为“可选向量检索 + 关键词 fallback”的本地 RAG 架构, 并支持 Windows 本地 Qdrant。

## 是否需要安装向量数据库

当前支持两种本地向量库模式:

1. 本地 JSON 向量索引: 不需要安装向量数据库。
2. Qdrant 本地向量数据库: Windows 推荐用 Docker 启动本地 Qdrant 服务。

选择建议:

- 想快速体验: 用本地 JSON。
- 想贴近正式本地向量数据库: 用 Qdrant。

## Windows 本地 Qdrant 准备

推荐 Docker:

```bash
docker run -p 6333:6333 -p 6334:6334 -v %cd%/qdrant_storage:/qdrant/storage qdrant/qdrant
```

Desktop 中配置:

- 向量库: `Qdrant`
- Qdrant URL: `http://localhost:6333`
- Qdrant Collection: `test_agent_desktop`

## Embedding 准备

如果要体验向量检索:

```bash
ollama pull nomic-embed-text
ollama serve
```

Desktop 中配置:

- Embedding 模型: `nomic-embed-text`
- Top-K: 例如 `5`
- 相似度阈值: 例如 `0.30`
- 勾选“启用向量检索”

如果本地没有 Ollama embedding 模型:

- 系统仍然可以使用关键词 fallback。
- 不会阻塞主流程。

## 架构设计

```text
RagEngine
  -> EmbeddingAdapter
      -> OllamaEmbeddingAdapter
  -> VectorIndex
      -> LocalVectorIndex(JSON)
      -> QdrantVectorIndex(REST)
  -> Keyword fallback
```

## P5 首版交付

- `EmbeddingAdapter` 接口。
- `OllamaEmbeddingAdapter`。
- `LocalVectorIndex`。
- `QdrantVectorIndex`。
- `RagEngine.import_markdown` 支持写入本地 JSON 或 Qdrant 向量索引。
- `RagEngine.retrieve` 支持 `top_k` 和 `similarity_threshold`。
- UI RAG 侧栏支持向量库选择、Embedding 模型、Top-K、相似度阈值、Qdrant URL、Collection。

## 验证

- 单元测试使用 FakeEmbeddingAdapter, 不依赖本地 Ollama。
- Qdrant 单元测试使用 FakeQdrantClient, 不依赖本地 Qdrant 服务。
- 验证 Top-K 和相似度阈值会改变召回结果。
- 编译检查通过。
