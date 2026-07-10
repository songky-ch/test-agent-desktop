import unittest

from app.rag.embeddings import OllamaEmbeddingAdapter


class FallbackEmbeddingHttpClient:
    def __init__(self):
        self.urls = []

    def post_json(self, url, headers, payload):
        self.urls.append(url)
        if url.endswith("/api/embed"):
            raise RuntimeError("HTTP 404: not found")
        return {"embedding": [1.0, 0.0]}


class FailingEmbeddingHttpClient:
    def post_json(self, url, headers, payload):
        raise RuntimeError("HTTP 404: model not found")


class OllamaEmbeddingTest(unittest.TestCase):
    def test_embedding_adapter_falls_back_to_legacy_endpoint(self):
        client = FallbackEmbeddingHttpClient()
        adapter = OllamaEmbeddingAdapter("nomic-embed-text", client)

        embedding = adapter.embed("手机号注册")

        self.assertEqual(embedding, [1.0, 0.0])
        self.assertTrue(client.urls[0].endswith("/api/embed"))
        self.assertTrue(client.urls[1].endswith("/api/embeddings"))

    def test_embedding_adapter_reports_install_command(self):
        adapter = OllamaEmbeddingAdapter("nomic-embed-text", FailingEmbeddingHttpClient())

        with self.assertRaisesRegex(RuntimeError, "ollama pull nomic-embed-text"):
            adapter.embed("手机号注册")


if __name__ == "__main__":
    unittest.main()
