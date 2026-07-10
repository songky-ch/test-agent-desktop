import tempfile
import unittest
from pathlib import Path

from app.rag.embeddings import EmbeddingAdapter
from app.rag.engine import RagEngine
from app.services.application_service import ApplicationService


class FakeEmbeddingAdapter(EmbeddingAdapter):
    def embed(self, text):
        if "注册" in text or "手机号" in text:
            return [1.0, 0.0]
        if "支付" in text:
            return [0.0, 1.0]
        return [0.5, 0.5]


class P5VectorRagTest(unittest.TestCase):
    def test_vector_retrieve_respects_top_k_and_threshold(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "knowledge.md"
            source.write_text(
                "# 知识库\n\n重复手机号注册应阻止\n\n支付失败需要提示用户",
                encoding="utf-8",
            )
            engine = RagEngine(
                root / "knowledge",
                embedding_adapter=FakeEmbeddingAdapter(),
                use_vector=True,
                similarity_threshold=0.8,
            )

            stats = engine.import_markdown(source)
            matches = engine.retrieve("手机号注册", top_k=1)

            self.assertEqual(stats.vector_count, 2)
            self.assertEqual(len(matches), 1)
            self.assertIn("重复手机号注册应阻止", matches[0])
            self.assertTrue((root / "knowledge" / "vector_index.json").exists())

    def test_remove_document_updates_local_vector_index(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "knowledge.md"
            source.write_text("# 知识库\n\n重复手机号注册应阻止", encoding="utf-8")
            engine = RagEngine(
                root / "knowledge",
                embedding_adapter=FakeEmbeddingAdapter(),
                use_vector=True,
            )

            engine.import_markdown(source)
            stats = engine.remove_document("knowledge.md")

            self.assertEqual(stats.vector_count, 0)

    def test_vector_threshold_filters_low_similarity_chunks(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "knowledge.md"
            source.write_text("# 知识库\n\n支付失败需要提示用户", encoding="utf-8")
            engine = RagEngine(
                root / "knowledge",
                embedding_adapter=FakeEmbeddingAdapter(),
                use_vector=True,
                similarity_threshold=0.99,
            )

            engine.import_markdown(source)
            matches = engine.retrieve("手机号注册", top_k=3)

            self.assertEqual(matches, [])

    def test_application_service_configures_vector_rag(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            service = ApplicationService(Path(temp_dir))

            service.configure_rag(
                top_k=3,
                similarity_threshold=0.6,
                embedding_model="nomic-embed-text",
                use_vector=True,
                embedding_adapter=FakeEmbeddingAdapter(),
            )

            self.assertEqual(service.rag.top_k, 3)
            self.assertEqual(service.rag.similarity_threshold, 0.6)
            self.assertTrue(service.rag.use_vector)

    def test_application_service_configures_qdrant_backend(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            service = ApplicationService(Path(temp_dir))

            service.configure_rag(
                top_k=5,
                similarity_threshold=0.3,
                embedding_model="nomic-embed-text",
                use_vector=True,
                vector_backend="qdrant",
                qdrant_url="http://localhost:6333",
                qdrant_collection="case_docs",
                embedding_adapter=FakeEmbeddingAdapter(),
            )

            self.assertEqual(service.rag.vector_backend, "qdrant")
            self.assertEqual(service.rag.qdrant_collection, "case_docs")


if __name__ == "__main__":
    unittest.main()
