from typing import Protocol


class EmbeddingAdapter(Protocol):
    def embed(self, text: str) -> list[float]:
        ...


class OllamaEmbeddingAdapter:
    def __init__(self, model: str, http_client):
        self.model = model
        self.http_client = http_client

    def embed(self, text: str) -> list[float]:
        response = self.http_client.post_json(
            "http://localhost:11434/api/embeddings",
            {"Content-Type": "application/json"},
            {"model": self.model, "prompt": text},
        )
        return response["embedding"]
