import json
import unittest

from app.agent.llm_provider import LlmMessage, OpenAiCompatibleProvider
from app.config.config_manager import ModelConfig


class FakeHttpClient:
    def __init__(self):
        self.request = None

    def post_json(self, url, headers, payload):
        self.request = {"url": url, "headers": headers, "payload": payload}
        return {"choices": [{"message": {"content": "模型返回内容"}}]}


class LlmProviderTest(unittest.TestCase):
    def test_openai_compatible_provider_sends_chat_completion_request(self):
        client = FakeHttpClient()
        provider = OpenAiCompatibleProvider(
            ModelConfig(
                source="openai_compatible",
                api_base_url="https://api.example.com/v1",
                api_key="sk-test",
                api_model="test-model",
            ),
            http_client=client,
        )

        result = provider.chat([LlmMessage(role="user", content="生成测试点")])

        self.assertEqual(result, "模型返回内容")
        self.assertEqual(client.request["url"], "https://api.example.com/v1/chat/completions")
        self.assertEqual(client.request["headers"]["Authorization"], "Bearer sk-test")
        self.assertEqual(client.request["payload"]["model"], "test-model")
        self.assertEqual(client.request["payload"]["messages"][0]["content"], "生成测试点")


if __name__ == "__main__":
    unittest.main()
