from dataclasses import asdict
from pathlib import Path
import json

from app.models.entities import TestCase, TestPoint


class ResultStore:
    def __init__(self, output_dir: Path):
        self.output_dir = Path(output_dir)

    def save_run(self, run_id: str, points: list[TestPoint], cases: list[TestCase]) -> Path:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        output = self.output_dir / f"{run_id}.json"
        payload = {
            "run_id": run_id,
            "test_points": [asdict(point) for point in points],
            "test_cases": [asdict(case) for case in cases],
        }
        output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return output

    def load_run(self, run_id: str) -> dict:
        path = self.output_dir / f"{run_id}.json"
        return json.loads(path.read_text(encoding="utf-8"))
