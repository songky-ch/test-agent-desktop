from dataclasses import dataclass
import json
import subprocess
from typing import Optional, Protocol
from urllib.error import HTTPError, URLError
from urllib import request

from app.config.config_manager import ModelConfig


@dataclass(frozen=True)
class LlmMessage:
    role: str
    content: str


class HttpClient(Protocol):
    def post_json(self, url: str, headers: dict[str, str], payload: dict):
        ...


class UrlLibHttpClient:
    def post_json(self, url: str, headers: dict[str, str], payload: dict):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = request.Request(url, data=body, headers=headers, method="POST")
        try:
            with request.urlopen(req, timeout=60) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"HTTP {exc.code}: {detail}") from exc
        except URLError as exc:
            raise RuntimeError(f"网络连接失败: {exc.reason}") from exc


class OpenAiCompatibleProvider:
    def __init__(self, config: ModelConfig, http_client: Optional[HttpClient] = None):
        self.config = config
        self.http_client = http_client or UrlLibHttpClient()

    def chat(self, messages: list[LlmMessage]) -> str:
        payload = {
            "model": self.config.api_model,
            "messages": [{"role": message.role, "content": message.content} for message in messages],
            "temperature": 0.2,
        }
        response = self.http_client.post_json(
            self._chat_url(),
            self._headers(),
            payload,
        )
        return response["choices"][0]["message"]["content"]

    def _chat_url(self) -> str:
        return self.config.api_base_url.rstrip("/") + "/chat/completions"

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"
        return headers


class OllamaAdapter:
    def __init__(self, config: ModelConfig, http_client: Optional[HttpClient] = None):
        self.config = config
        self.http_client = http_client or UrlLibHttpClient()

    def list_models(self) -> list[str]:
        try:
            result = subprocess.run(
                ["ollama", "list"],
                check=False,
                capture_output=True,
                text=True,
            )
        except FileNotFoundError:
            return []
        if result.returncode != 0:
            return []
        lines = [line.split() for line in result.stdout.splitlines()[1:] if line.strip()]
        return [parts[0] for parts in lines if parts]

    def chat(self, messages: list[LlmMessage]) -> str:
        if "embed" in self.config.ollama_model.lower():
            raise RuntimeError("当前选择的是 embedding 模型, 不能用于生成测试点/用例。请在模型配置中选择对话模型, 例如 qwen、llama、mistral 等。")
        payload = {
            "model": self.config.ollama_model,
            "messages": [{"role": message.role, "content": message.content} for message in messages],
            "stream": False,
        }
        try:
            response = self.http_client.post_json(
                "http://localhost:11434/api/chat",
                {"Content-Type": "application/json"},
                payload,
            )
            return response["message"]["content"]
        except Exception:
            return self._generate(messages)

    def _generate(self, messages: list[LlmMessage]) -> str:
        prompt = "\n".join(f"{message.role}: {message.content}" for message in messages)
        response = self.http_client.post_json(
            "http://localhost:11434/api/generate",
            {"Content-Type": "application/json"},
            {
                "model": self.config.ollama_model,
                "prompt": prompt,
                "stream": False,
            },
        )
        return response["response"]


class ModelRouter:
    def __init__(self, config: ModelConfig, http_client: Optional[HttpClient] = None):
        self.config = config
        self.http_client = http_client

    def provider(self):
        if self.config.source == "ollama":
            return OllamaAdapter(self.config, self.http_client)
        return OpenAiCompatibleProvider(self.config, self.http_client)

    def chat(self, messages: list[LlmMessage]) -> str:
        return self.provider().chat(messages)
