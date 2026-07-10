import unittest

from app.rag.qdrant_index import QdrantVectorIndex


class FakeQdrantClient:
    def __init__(self):
        self.calls = []
        self.points = []

    def request_json(self, method, url, payload=None):
        self.calls.append({"method": method, "url": url, "payload": payload})
        if url.endswith("/points") and method == "PUT":
            self.points = payload["points"]
            return {"status": "ok"}
        if url.endswith("/points/search"):
            threshold = payload["score_threshold"]
            limit = payload["limit"]
            result = [
                {"payload": {"chunk": self.points[0]["payload"]["chunk"]}, "score": 0.91},
                {"payload": {"chunk": self.points[1]["payload"]["chunk"]}, "score": 0.41},
            ]
            return {
                "result": [item for item in result if item["score"] >= threshold][:limit]
            }
        if url.endswith("/points/count"):
            return {"result": {"count": len(self.points)}}
        return {"status": "ok"}


class QdrantVectorIndexTest(unittest.TestCase):
    def test_qdrant_index_creates_collection_upserts_and_searches(self):
        client = FakeQdrantClient()
        index = QdrantVectorIndex(
            base_url="http://localhost:6333",
            collection_name="test_agent",
            project_id="project-a",
            http_client=client,
        )

        index.save_document(
            "knowledge.md",
            ["重复手机号注册应阻止", "支付失败需要提示"],
            [[1.0, 0.0], [0.0, 1.0]],
        )
        matches = index.search([1.0, 0.0], top_k=1, threshold=0.8)

        self.assertEqual(matches, ["重复手机号注册应阻止"])
        self.assertEqual(index.count(), 2)
        self.assertEqual(client.calls[0]["method"], "PUT")
        self.assertIn("/collections/test_agent", client.calls[0]["url"])
        self.assertEqual(client.points[0]["payload"]["project_id"], "project-a")
        self.assertEqual(client.calls[2]["payload"]["filter"]["must"][0]["match"]["value"], "project-a")


if __name__ == "__main__":
    unittest.main()
