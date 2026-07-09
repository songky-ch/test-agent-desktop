import tempfile
import unittest
from pathlib import Path

from app.rag.engine import RagEngine


class RagEngineTest(unittest.TestCase):
    def test_import_document_builds_chunks_and_retrieves_top_matches(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "history.md"
            source.write_text("# 历史缺陷\n重复手机号注册应阻止\n支付失败需要提示", encoding="utf-8")
            engine = RagEngine(root / "knowledge")

            index = engine.import_markdown(source)
            matches = engine.retrieve("手机号 注册", top_k=1)

            self.assertEqual(index.document_count, 1)
            self.assertGreaterEqual(index.chunk_count, 1)
            self.assertIn("重复手机号注册应阻止", matches[0])
            self.assertTrue((root / "knowledge" / "index.json").exists())


if __name__ == "__main__":
    unittest.main()
