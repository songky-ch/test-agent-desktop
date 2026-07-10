from dataclasses import asdict, dataclass
from pathlib import Path
import json
from typing import Optional, Protocol


class SecretStore(Protocol):
    def set_password(self, service_name: str, username: str, password: str) -> None:
        ...

    def get_password(self, service_name: str, username: str) -> Optional[str]:
        ...


class KeyringSecretStore:
    def __init__(self):
        import keyring

        self.keyring = keyring

    def set_password(self, service_name: str, username: str, password: str) -> None:
        self.keyring.set_password(service_name, username, password)

    def get_password(self, service_name: str, username: str) -> Optional[str]:
        return self.keyring.get_password(service_name, username)


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
    service_name = "test-agent-desktop"

    def __init__(self, config_path: Path, secret_store: Optional[SecretStore] = None):
        self.config_path = Path(config_path)
        self.secret_store = secret_store if secret_store is not None else self._default_secret_store()

    def save_model_config(self, config: ModelConfig) -> None:
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        data = asdict(config)
        if config.source == "openai_compatible" and config.api_key and self._save_secret(config.api_key):
            data["api_key"] = ""
            data["api_key_storage"] = "keyring"
        self.config_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def load_model_config(self) -> ModelConfig:
        if not self.config_path.exists():
            return ModelConfig()
        data = json.loads(self.config_path.read_text(encoding="utf-8"))
        config = self._normalize_config(data)
        if config.source == "openai_compatible" and not config.api_key:
            secret = self._load_secret()
            if secret:
                return ModelConfig(
                    source=config.source,
                    ollama_model=config.ollama_model,
                    api_base_url=config.api_base_url,
                    api_key=secret,
                    api_model=config.api_model,
                )
        return config

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

    def _secret_username(self) -> str:
        return str(self.config_path)

    def _save_secret(self, api_key: str) -> bool:
        if self.secret_store is None:
            return False
        try:
            self.secret_store.set_password(self.service_name, self._secret_username(), api_key)
        except Exception:
            return False
        return True

    def _load_secret(self) -> Optional[str]:
        if self.secret_store is None:
            return None
        try:
            return self.secret_store.get_password(self.service_name, self._secret_username())
        except Exception:
            return None

    def _default_secret_store(self) -> Optional[SecretStore]:
        try:
            return KeyringSecretStore()
        except Exception:
            return None
