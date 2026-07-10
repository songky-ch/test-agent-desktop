from dataclasses import dataclass
import hashlib
import json
from typing import Optional, Protocol
from urllib.error import HTTPError, URLError
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
        try:
            with request.urlopen(req, timeout=60) as response:
                body = response.read().decode("utf-8")
                return json.loads(body) if body else {}
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Qdrant HTTP {exc.code}: {detail}") from exc
        except URLError as exc:
            raise RuntimeError(f"Qdrant 连接失败: {exc.reason}") from exc


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

    def remove_document(self, document: str) -> None:
        self.http_client.request_json(
            "POST",
            f"{self._collection_url()}/points/delete",
            {
                "filter": {
                    "must": [
                        {"key": "project_id", "match": {"value": self.project_id}},
                        {"key": "document", "match": {"value": document}},
                    ]
                }
            },
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
        try:
            response = self.http_client.request_json(
                "POST",
                f"{self._collection_url()}/points/count",
                {
                    "exact": True,
                    "filter": {"must": [{"key": "project_id", "match": {"value": self.project_id}}]},
                },
            )
        except Exception as exc:
            if "HTTP 404" in str(exc):
                return 0
            raise
        return int(response.get("result", {}).get("count", 0))

    def ping(self) -> None:
        self.http_client.request_json("GET", f"{self.base_url}/collections")

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
