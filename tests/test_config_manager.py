import tempfile
import unittest
from pathlib import Path

from app.config.config_manager import ConfigManager, ModelConfig


class FakeSecretStore:
    def __init__(self):
        self.values = {}

    def set_password(self, service_name, username, password):
        self.values[(service_name, username)] = password

    def get_password(self, service_name, username):
        return self.values.get((service_name, username))


class ConfigManagerTest(unittest.TestCase):
    def test_model_config_masks_api_key(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = ConfigManager(Path(temp_dir) / "config.yaml", secret_store=None)
            config = ModelConfig(
                source="openai_compatible",
                api_base_url="https://api.example.com/v1",
                api_key="sk-1234567890",
                api_model="test-model",
            )

            manager.save_model_config(config)
            loaded = manager.load_model_config()

            self.assertEqual(loaded, config)
            self.assertEqual(loaded.masked_api_key, "sk-1******7890")

    def test_model_config_stores_api_key_in_secret_store_when_available(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.json"
            manager = ConfigManager(config_path, secret_store=FakeSecretStore())
            config = ModelConfig(
                source="openai_compatible",
                api_base_url="https://api.example.com/v1",
                api_key="sk-secret",
                api_model="test-model",
            )

            manager.save_model_config(config)
            raw = config_path.read_text(encoding="utf-8")
            loaded = manager.load_model_config()

            self.assertNotIn("sk-secret", raw)
            self.assertEqual(loaded.api_key, "sk-secret")


if __name__ == "__main__":
    unittest.main()
