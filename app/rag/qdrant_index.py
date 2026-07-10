from dataclasses import dataclass
import hashlib
import json
from typing import Optional, Protocol
from urllib import request


class QdrantHttpClient(Protocol):
    def request_json(self, method: str, url: str, payload: Optional[dict] = None):
        ...


class UrlLibQdrantClient:
    def request_json(self, method: str, url: str, payload: Optional[dict] = None):
        data = None
        if payload is not None:
            data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method=method,
        )
        with request.urlopen(req, timeout=60) as response:
            body = response.read().decode("utf-8")
            return json.loads(body) if body else {}


@dataclass(frozen=True)
class QdrantPoint:
    id: str
    vector: list[float]
    payload: dict


class QdrantVectorIndex:
    def __init__(
        self,
        base_url: str,
        collection_name: str,
        project_id: str = "default",
        http_client: Optional[QdrantHttpClient] = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.collection_name = collection_name
        self.project_id = project_id
        self.http_client = http_client or UrlLibQdrantClient()

    def save_document(self, document: str, chunks: list[str], embeddings: list[list[float]]) -> None:
        if not embeddings:
            return
        self._ensure_collection(len(embeddings[0]))
        points = []
        for chunk, embedding in zip(chunks, embeddings):
            points.append(
                {
                    "id": self._point_id(document, chunk),
                    "vector": embedding,
                    "payload": {"project_id": self.project_id, "document": document, "chunk": chunk},
                }
            )
        self.http_client.request_json(
            "PUT",
            f"{self._collection_url()}/points",
            {"points": points},
        )

    def search(self, query_embedding: list[float], top_k: int, threshold: float) -> list[str]:
        response = self.http_client.request_json(
            "POST",
            f"{self._collection_url()}/points/search",
            {
                "vector": query_embedding,
                "limit": top_k,
                "score_threshold": threshold,
                "with_payload": True,
                "filter": {"must": [{"key": "project_id", "match": {"value": self.project_id}}]},
            },
        )
        return [item["payload"]["chunk"] for item in response.get("result", [])]

    def count(self) -> int:
        response = self.http_client.request_json(
            "POST",
            f"{self._collection_url()}/points/count",
            {"exact": True},
        )
        return int(response.get("result", {}).get("count", 0))

    def _ensure_collection(self, vector_size: int) -> None:
        self.http_client.request_json(
            "PUT",
            self._collection_url(),
            {"vectors": {"size": vector_size, "distance": "Cosine"}},
        )

    def _collection_url(self) -> str:
        return f"{self.base_url}/collections/{self.collection_name}"

    def _point_id(self, document: str, chunk: str) -> str:
        digest = hashlib.md5(f"{document}:{chunk}".encode("utf-8")).hexdigest()
        return digest
