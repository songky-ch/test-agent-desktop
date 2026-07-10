import json
import unittest

from app.agent.llm_provider import LlmMessage, OllamaAdapter, OpenAiCompatibleProvider
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

    def test_ollama_provider_falls_back_to_generate_when_chat_fails(self):
        class FallbackHttpClient:
            def __init__(self):
                self.urls = []

            def post_json(self, url, headers, payload):
                self.urls.append(url)
                if url.endswith("/api/chat"):
                    raise RuntimeError("HTTP 500: model does not support chat")
                return {"response": "pong"}

        client = FallbackHttpClient()
        provider = OllamaAdapter(ModelConfig(source="ollama", ollama_model="local-model"), client)

        result = provider.chat([LlmMessage(role="user", content="ping")])

        self.assertEqual(result, "pong")
        self.assertTrue(client.urls[0].endswith("/api/chat"))
        self.assertTrue(client.urls[1].endswith("/api/generate"))

    def test_ollama_provider_rejects_embedding_model_for_generation(self):
        provider = OllamaAdapter(ModelConfig(source="ollama", ollama_model="nomic-embed-text"))

        with self.assertRaisesRegex(RuntimeError, "embedding 模型"):
            provider.chat([LlmMessage(role="user", content="ping")])


if __name__ == "__main__":
    unittest.main()
