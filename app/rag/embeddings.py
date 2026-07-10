from typing import Protocol


class EmbeddingAdapter(Protocol):
    def embed(self, text: str) -> list[float]:
        ...


class OllamaEmbeddingAdapter:
    def __init__(self, model: str, http_client):
        self.model = model
        self.http_client = http_client

    def embed(self, text: str) -> list[float]:
        try:
            response = self.http_client.post_json(
                "http://localhost:11434/api/embed",
                {"Content-Type": "application/json"},
                {"model": self.model, "input": text},
            )
            embeddings = response.get("embeddings", [])
            if embeddings:
                return embeddings[0]
        except Exception:
            pass

        try:
            response = self.http_client.post_json(
                "http://localhost:11434/api/embeddings",
                {"Content-Type": "application/json"},
                {"model": self.model, "prompt": text},
            )
        except Exception as exc:
            raise RuntimeError(
                f"Ollama embedding 不可用。请确认已执行: ollama pull {self.model}, "
                f"并确认 ollama serve 正在运行。原始错误: {exc}"
            ) from exc
        return response["embedding"]
