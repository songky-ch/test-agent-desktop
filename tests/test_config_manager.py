import tempfile
import unittest
from pathlib import Path

from app.config.config_manager import ConfigManager, ModelConfig


class ConfigManagerTest(unittest.TestCase):
    def test_model_config_masks_api_key(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = ConfigManager(Path(temp_dir) / "config.yaml")
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


if __name__ == "__main__":
    unittest.main()
