import tempfile
import unittest
from pathlib import Path

from app.skills.runtime import SkillRuntime


class SkillRuntimeTest(unittest.TestCase):
    def test_skill_runtime_loads_directory_skill(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill_dir = root / "skills" / "generate_test_cases"
            skill_dir.mkdir(parents=True)
            (skill_dir / "skill.yaml").write_text(
                "name: generate_test_cases\n"
                "description: 生成测试用例\n"
                "entry: handler.py\n",
                encoding="utf-8",
            )
            (skill_dir / "prompt.md").write_text("按模板生成测试用例", encoding="utf-8")
            (skill_dir / "handler.py").write_text(
                "def run(payload):\n"
                "    return {'received': payload['name']}\n",
                encoding="utf-8",
            )

            runtime = SkillRuntime(root / "skills")

            self.assertEqual([skill.name for skill in runtime.list_skills()], ["generate_test_cases"])
            self.assertEqual(runtime.invoke("generate_test_cases", {"name": "case"}), {"received": "case"})


if __name__ == "__main__":
    unittest.main()
