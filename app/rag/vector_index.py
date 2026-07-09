from dataclasses import dataclass
from pathlib import Path
import json
import math


@dataclass(frozen=True)
class VectorRecord:
    document: str
    chunk: str
    embedding: list[float]


class LocalVectorIndex:
    def __init__(self, index_path: Path):
        self.index_path = Path(index_path)

    def save_document(self, document: str, chunks: list[str], embeddings: list[list[float]]) -> None:
        records = [record for record in self._load_records() if record.document != document]
        records.extend(VectorRecord(document=document, chunk=chunk, embedding=embedding) for chunk, embedding in zip(chunks, embeddings))
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        payload = [record.__dict__ for record in records]
        self.index_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def search(self, query_embedding: list[float], top_k: int, threshold: float) -> list[str]:
        scored = []
        for record in self._load_records():
            score = self._cosine_similarity(query_embedding, record.embedding)
            if score >= threshold:
                scored.append((score, record.chunk))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [chunk for _, chunk in scored[:top_k]]

    def count(self) -> int:
        return len(self._load_records())

    def _load_records(self) -> list[VectorRecord]:
        if not self.index_path.exists():
            return []
        payload = json.loads(self.index_path.read_text(encoding="utf-8"))
        return [VectorRecord(**item) for item in payload]

    def _cosine_similarity(self, left: list[float], right: list[float]) -> float:
        if not left or not right:
            return 0.0
        size = min(len(left), len(right))
        dot = sum(left[index] * right[index] for index in range(size))
        left_norm = math.sqrt(sum(value * value for value in left[:size]))
        right_norm = math.sqrt(sum(value * value for value in right[:size]))
        if not left_norm or not right_norm:
            return 0.0
        return dot / (left_norm * right_norm)
