from pathlib import Path
from dataclasses import dataclass
import json
from typing import Optional

from app.rag.embeddings import EmbeddingAdapter
from app.rag.qdrant_index import QdrantHttpClient, QdrantVectorIndex
from app.rag.vector_index import LocalVectorIndex


@dataclass(frozen=True)
class RagIndexStats:
    document_count: int
    chunk_count: int
    index_path: Path
    vector_count: int = 0
    vector_index_path: Optional[Path] = None


class RagEngine:
    def __init__(
        self,
        knowledge_dir: Path,
        embedding_adapter: Optional[EmbeddingAdapter] = None,
        use_vector: bool = False,
        similarity_threshold: float = 0.3,
        vector_backend: str = "local",
        qdrant_url: str = "http://localhost:6333",
        qdrant_collection: str = "test_agent_desktop",
        project_id: str = "default",
        qdrant_client: Optional[QdrantHttpClient] = None,
    ):
        self.knowledge_dir = Path(knowledge_dir)
        self.enabled = True
        self.top_k = 5
        self.embedding_adapter = embedding_adapter
        self.use_vector = use_vector
        self.similarity_threshold = similarity_threshold
        self.vector_backend = vector_backend
        self.qdrant_url = qdrant_url
        self.qdrant_collection = qdrant_collection
        self.project_id = project_id
        self.qdrant_client = qdrant_client
        self.vector_index = self._create_vector_index()

    def import_markdown(self, source_path: Path) -> RagIndexStats:
        source = Path(source_path)
        self.knowledge_dir.mkdir(parents=True, exist_ok=True)
        target = self.knowledge_dir / source.name
        content = source.read_text(encoding="utf-8")
        target.write_text(content, encoding="utf-8")

        chunks = self._chunk(content)
        documents = self._load_index()
        documents[source.name] = chunks
        self._save_index(documents)
        if self.use_vector and self.embedding_adapter:
            embeddings = [self.embedding_adapter.embed(chunk) for chunk in chunks]
            self.vector_index.save_document(source.name, chunks, embeddings)
        return RagIndexStats(
            document_count=len(documents),
            chunk_count=sum(len(items) for items in documents.values()),
            index_path=self._index_path(),
            vector_count=self.vector_index.count(),
            vector_index_path=self._vector_index_path(),
        )

    def remove_document(self, document: str) -> RagIndexStats:
        documents = self._load_index()
        documents.pop(Path(document).name, None)
        target = self.knowledge_dir / Path(document).name
        if target.exists():
            target.unlink()
        self._save_index(documents)
        if hasattr(self.vector_index, "remove_document"):
            self.vector_index.remove_document(Path(document).name)
        return self.stats()

    def retrieve(self, query: str, top_k: Optional[int] = None) -> list[str]:
        if not self.enabled or not self.knowledge_dir.exists():
            return []

        limit = top_k or self.top_k
        if self.use_vector and self.embedding_adapter and self.vector_index.count():
            query_embedding = self.embedding_adapter.embed(query)
            return self.vector_index.search(query_embedding, limit, self.similarity_threshold)

        scored = []
        terms = self._terms(query)
        documents = self._load_index()
        for chunks in documents.values():
            for content in chunks:
                score = self._score(content, terms)
                if score:
                    scored.append((score, content))
        if not scored:
            for path in self.knowledge_dir.glob("*.md"):
                content = path.read_text(encoding="utf-8")
                score = self._score(content, terms)
                if score:
                    scored.append((score, content[:800]))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [content for _, content in scored[:limit]]

    def stats(self) -> RagIndexStats:
        documents = self._load_index()
        return RagIndexStats(
            document_count=len(documents),
            chunk_count=sum(len(items) for items in documents.values()),
            index_path=self._index_path(),
            vector_count=self.vector_index.count(),
            vector_index_path=self._vector_index_path(),
        )

    def test_vector_backend(self) -> None:
        if self.vector_backend == "qdrant" and hasattr(self.vector_index, "ping"):
            self.vector_index.ping()

    def _chunk(self, content: str, chunk_size: int = 700) -> list[str]:
        paragraphs = [part.strip() for part in content.split("\n\n") if part.strip() and not part.strip().startswith("#")]
        if all(len(paragraph) <= chunk_size for paragraph in paragraphs):
            return paragraphs or [content]
        chunks = []
        current = ""
        for paragraph in paragraphs:
            if current and len(current) + len(paragraph) > chunk_size:
                chunks.append(current)
                current = paragraph
            else:
                current = f"{current}\n\n{paragraph}".strip()
        if current:
            chunks.append(current)
        return chunks or [content]

    def _terms(self, query: str) -> set[str]:
        normalized = query.replace("\n", " ").replace(",", " ").replace("，", " ")
        return {term for term in normalized.split(" ") if term}

    def _score(self, content: str, terms: set[str]) -> int:
        score = sum(1 for term in terms if term in content)
        if not score:
            compact = content.replace(" ", "")
            score = sum(1 for term in terms if term and term in compact)
        return score

    def _index_path(self) -> Path:
        return self.knowledge_dir / "index.json"

    def _vector_index_path(self) -> Path:
        return self.knowledge_dir / "vector_index.json"

    def _create_vector_index(self):
        if self.vector_backend == "qdrant":
            return QdrantVectorIndex(
                base_url=self.qdrant_url,
                collection_name=self.qdrant_collection,
                project_id=self.project_id,
                http_client=self.qdrant_client,
            )
        return LocalVectorIndex(self._vector_index_path())

    def _load_index(self) -> dict[str, list[str]]:
        index_path = self._index_path()
        if not index_path.exists():
            return {}
        return json.loads(index_path.read_text(encoding="utf-8"))

    def _save_index(self, documents: dict[str, list[str]]) -> None:
        index_path = self._index_path()
        index_path.write_text(json.dumps(documents, ensure_ascii=False, indent=2), encoding="utf-8")
