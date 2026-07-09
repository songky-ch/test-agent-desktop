import tempfile
import unittest
from pathlib import Path

from app.documents.pipeline import DocumentPipeline


class DocumentPipelineTest(unittest.TestCase):
    def test_txt_document_converts_to_markdown(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "requirement.txt"
            source.write_text("用户注册\n手机号必填", encoding="utf-8")
            output_dir = root / "markdown"

            result = DocumentPipeline(output_dir).convert_to_markdown(source)

            self.assertEqual(result.source_path, source)
            self.assertEqual(result.markdown_path, output_dir / "requirement.md")
            self.assertEqual(result.content, "# requirement\n\n用户注册\n手机号必填")
            self.assertEqual(result.markdown_path.read_text(encoding="utf-8"), result.content)

    def test_md_document_is_normalized_and_copied(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "story.md"
            source.write_text("# 原始需求\n\n支持登录", encoding="utf-8")

            result = DocumentPipeline(root / "markdown").convert_to_markdown(source)

            self.assertEqual(result.content, "# 原始需求\n\n支持登录")
            self.assertEqual(result.markdown_path.name, "story.md")


if __name__ == "__main__":
    unittest.main()
