import tempfile
import unittest
from pathlib import Path

from app.services.application_service import ApplicationService


class P6SkillIntegrationTest(unittest.TestCase):
    def test_application_service_lists_and_runs_skill_with_result_store(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill_dir = root / "skills" / "analyze_defects"
            skill_dir.mkdir(parents=True)
            (skill_dir / "skill.yaml").write_text(
                "name: analyze_defects\n"
                "description: 分析缺陷记录\n"
                "entry: handler.py\n",
                encoding="utf-8",
            )
            (skill_dir / "prompt.md").write_text("分析缺陷记录", encoding="utf-8")
            (skill_dir / "handler.py").write_text(
                "def run(payload):\n"
                "    return {'summary': '共发现 1 个高频缺陷', 'input_count': len(payload.get('items', []))}\n",
                encoding="utf-8",
            )
            service = ApplicationService(root)

            skills = service.list_skills()
            result = service.run_skill("analyze_defects", {"items": ["登录失败"]})

            self.assertEqual(skills[0].name, "analyze_defects")
            self.assertTrue(result["ok"])
            self.assertEqual(result["result"]["summary"], "共发现 1 个高频缺陷")
            self.assertTrue((root / "data" / "outputs" / "skills" / "analyze_defects.json").exists())

    def test_application_service_returns_structured_skill_error(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill_dir = root / "skills" / "broken_skill"
            skill_dir.mkdir(parents=True)
            (skill_dir / "skill.yaml").write_text(
                "name: broken_skill\n"
                "description: 异常 Skill\n"
                "entry: handler.py\n",
                encoding="utf-8",
            )
            (skill_dir / "handler.py").write_text(
                "def run(payload):\n"
                "    raise ValueError('输入不完整')\n",
                encoding="utf-8",
            )
            service = ApplicationService(root)

            result = service.run_skill("broken_skill", {})

            self.assertFalse(result["ok"])
            self.assertEqual(result["error_type"], "ValueError")
            self.assertEqual(result["message"], "输入不完整")


if __name__ == "__main__":
    unittest.main()
