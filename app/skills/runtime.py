from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from types import ModuleType

from app.models.entities import Skill


class SkillRuntime:
    def __init__(self, skills_dir: Path):
        self.skills_dir = Path(skills_dir)

    def list_skills(self) -> list[Skill]:
        if not self.skills_dir.exists():
            return []
        skills = []
        for path in sorted(self.skills_dir.iterdir()):
            manifest = path / "skill.yaml"
            if path.is_dir() and manifest.exists():
                metadata = self._read_manifest(manifest)
                skills.append(
                    Skill(
                        name=metadata.get("name", path.name),
                        description=metadata.get("description", ""),
                        entry=metadata.get("entry", "handler.py"),
                        prompt=self._read_prompt(path),
                        path=path,
                    )
                )
        return skills

    def invoke(self, skill_name: str, payload: dict):
        skill = self._find_skill(skill_name)
        module = self._load_module(skill.path / skill.entry)
        return module.run(payload)

    def _find_skill(self, skill_name: str) -> Skill:
        for skill in self.list_skills():
            if skill.name == skill_name:
                return skill
        raise ValueError(f"Skill not found: {skill_name}")

    def _read_manifest(self, manifest: Path) -> dict[str, str]:
        metadata = {}
        for line in manifest.read_text(encoding="utf-8").splitlines():
            if ":" in line:
                key, value = line.split(":", 1)
                metadata[key.strip()] = value.strip().strip('"').strip("'")
        return metadata

    def _read_prompt(self, skill_path: Path) -> str:
        prompt = skill_path / "prompt.md"
        if not prompt.exists():
            return ""
        return prompt.read_text(encoding="utf-8")

    def _load_module(self, path: Path) -> ModuleType:
        spec = spec_from_file_location(f"skill_{path.parent.name}", path)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"Cannot load skill handler: {path}")
        module = module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
