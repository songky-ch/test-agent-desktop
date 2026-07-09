from dataclasses import asdict, dataclass
from pathlib import Path
import json


@dataclass(frozen=True)
class ModelConfig:
    source: str = "ollama"
    ollama_model: str = ""
    api_base_url: str = ""
    api_key: str = ""
    api_model: str = ""

    @property
    def masked_api_key(self) -> str:
        if self.source != "openai_compatible":
            return ""
        if not self.api_key:
            return ""
        if len(self.api_key) <= 8:
            return "*" * len(self.api_key)
        return f"{self.api_key[:4]}******{self.api_key[-4:]}"

    @property
    def display_name(self) -> str:
        if self.source == "ollama":
            return self.ollama_model or "未选择 Ollama 模型"
        return self.api_model or "未配置 API 模型"


class ConfigManager:
    def __init__(self, config_path: Path):
        self.config_path = Path(config_path)

    def save_model_config(self, config: ModelConfig) -> None:
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.config_path.write_text(json.dumps(asdict(config), ensure_ascii=False, indent=2), encoding="utf-8")

    def load_model_config(self) -> ModelConfig:
        if not self.config_path.exists():
            return ModelConfig()
        data = json.loads(self.config_path.read_text(encoding="utf-8"))
        return self._normalize_config(data)

    def _normalize_config(self, data: dict) -> ModelConfig:
        if "source" in data:
            allowed = {field.name for field in ModelConfig.__dataclass_fields__.values()}
            return ModelConfig(**{key: value for key, value in data.items() if key in allowed})

        provider = data.get("provider", "")
        use_ollama = data.get("use_ollama", provider == "Ollama")
        if use_ollama:
            return ModelConfig(source="ollama", ollama_model=data.get("model", ""))
        return ModelConfig(
            source="openai_compatible",
            api_base_url=data.get("base_url", ""),
            api_key=data.get("api_key", ""),
            api_model=data.get("model", ""),
        )
