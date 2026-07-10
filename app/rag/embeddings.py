from typing import Optional, Protocol


class EmbeddingAdapter(Protocol):
    def embed(self, text: str) -> list[float]:
        ...


class OllamaEmbeddingAdapter:
    def __init__(self, model: str, http_client):
        self.model = model.strip()
        self.http_client = http_client

    def embed(self, text: str) -> list[float]:
        primary_error = None
        try:
            response = self.http_client.post_json(
                "http://localhost:11434/api/embed",
                {"Content-Type": "application/json"},
                {"model": self.model, "input": text},
            )
            embeddings = response.get("embeddings", [])
            if embeddings:
                return embeddings[0]
        except Exception as exc:
            primary_error = exc
            message = str(exc).lower()
            if "model" in message and "not found" in message:
                raise self._unavailable_error(exc) from exc
            if "404" not in message:
                raise self._unavailable_error(exc) from exc

        try:
            response = self.http_client.post_json(
                "http://localhost:11434/api/embeddings",
                {"Content-Type": "application/json"},
                {"model": self.model, "prompt": text},
            )
        except Exception as exc:
            raise self._unavailable_error(exc, primary_error) from exc
        embedding = response.get("embedding", [])
        if not embedding:
            raise self._unavailable_error(RuntimeError("旧版接口未返回 embedding"), primary_error)
        return embedding

    def _unavailable_error(self, error: Exception, primary_error: Optional[Exception] = None) -> RuntimeError:
        details = f"新版接口: {primary_error}; 旧版接口: {error}" if primary_error else str(error)
        return RuntimeError(
            f"Ollama Embedding 模型 '{self.model}' 调用失败。请执行 ollama show {self.model} 验证模型, "
            f"模型不存在时执行 ollama pull {self.model}, "
            f"并确认应用连接的是 http://localhost:11434。错误详情: {details}"
        )
