"""LLM 适配器

统一封装 OpenAI 兼容接口（DeepSeek/Qwen/Kimi/OpenAI/本地 Ollama 兼容网关）。
adapter 只做"调用 LLM 拿到文本"这一件事，业务逻辑全部在 engine_llm.py / pipeline.py。

支持的 interface_format：
    - "openai"  : 标准 OpenAI Chat Completions /v1/chat/completions
    - "ollama"  : 本地 Ollama /api/chat（兼容 OpenAI 字段，做轻量适配）

设计要点：
    - 仅依赖 requests，避免引入 openai SDK 的版本耦合
    - 流式与非流式都支持
    - 失败时抛出 LLMAPIError，由上层决定是否回落到离线引擎
"""
from __future__ import annotations

import json
from typing import List, Dict, Optional, Iterator
from dataclasses import dataclass

try:
    import requests
except ImportError as e:  # pragma: no cover
    raise ImportError("LLM 适配器需要 requests：pip install requests") from e


class LLMAPIError(RuntimeError):
    """LLM 调用失败"""


@dataclass
class LLMResponse:
    text: str
    usage: Dict = None
    raw: Dict = None


class LLMAdapter:
    """LLM 统一适配器"""

    def __init__(self, api_key: str, base_url: str, model_name: str,
                 interface_format: str = "openai",
                 temperature: float = 0.8, max_tokens: int = 4096,
                 timeout: int = 60):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model_name
        self.interface = interface_format
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout

    # ---------- 公共入口 ----------
    def chat(self, messages: List[Dict[str, str]],
             stream: bool = False, **kwargs) -> LLMResponse | Iterator[str]:
        """统一聊天接口"""
        if self.interface == "ollama":
            return self._chat_ollama(messages, stream, **kwargs)
        return self._chat_openai(messages, stream, **kwargs)

    def generate(self, prompt: str, system: str = "",
                 stream: bool = False, **kwargs) -> str | Iterator[str]:
        """便捷入口：单 prompt → 文本"""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        if stream:
            return self._stream_text(messages, **kwargs)
        resp = self.chat(messages, stream=False, **kwargs)
        return resp.text

    # ---------- OpenAI 兼容 ----------
    def _chat_openai(self, messages, stream, **kwargs) -> LLMResponse | Iterator[str]:
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": kwargs.get("temperature", self.temperature),
            "max_tokens": kwargs.get("max_tokens", self.max_tokens),
            "stream": stream,
        }
        if stream:
            return self._iter_openai_stream(url, headers, payload)
        resp = requests.post(url, headers=headers, json=payload, timeout=self.timeout)
        if resp.status_code != 200:
            raise LLMAPIError(f"OpenAI 接口 {resp.status_code}: {resp.text[:300]}")
        data = resp.json()
        text = data["choices"][0]["message"]["content"]
        return LLMResponse(text=text, usage=data.get("usage"), raw=data)

    def _iter_openai_stream(self, url, headers, payload) -> Iterator[str]:
        payload["stream"] = True
        with requests.post(url, headers=headers, json=payload, stream=True, timeout=self.timeout) as r:
            if r.status_code != 200:
                raise LLMAPIError(f"OpenAI 流式 {r.status_code}: {r.text[:300]}")
            for line in r.iter_lines():
                if not line:
                    continue
                line = line.decode("utf-8")
                if line.startswith("data: "):
                    line = line[6:]
                if line.strip() == "[DONE]":
                    break
                try:
                    chunk = json.loads(line)
                    delta = chunk["choices"][0].get("delta", {}).get("content", "")
                    if delta:
                        yield delta
                except (json.JSONDecodeError, KeyError, IndexError):
                    continue

    # ---------- Ollama ----------
    def _chat_ollama(self, messages, stream, **kwargs) -> LLMResponse | Iterator[str]:
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": stream,
            "options": {
                "temperature": kwargs.get("temperature", self.temperature),
                "num_predict": kwargs.get("max_tokens", self.max_tokens),
            },
        }
        if stream:
            return self._iter_ollama_stream(url, payload)
        resp = requests.post(url, json=payload, timeout=self.timeout)
        if resp.status_code != 200:
            raise LLMAPIError(f"Ollama 接口 {resp.status_code}: {resp.text[:300]}")
        data = resp.json()
        return LLMResponse(text=data.get("message", {}).get("content", ""),
                           usage=None, raw=data)

    def _iter_ollama_stream(self, url, payload) -> Iterator[str]:
        with requests.post(url, json=payload, stream=True, timeout=self.timeout) as r:
            if r.status_code != 200:
                raise LLMAPIError(f"Ollama 流式 {r.status_code}: {r.text[:300]}")
            for line in r.iter_lines():
                if not line:
                    continue
                try:
                    chunk = json.loads(line.decode("utf-8"))
                    piece = chunk.get("message", {}).get("content", "")
                    if piece:
                        yield piece
                    if chunk.get("done"):
                        break
                except (json.JSONDecodeError, KeyError):
                    continue

    def _stream_text(self, messages, **kwargs):
        """统一流式文本迭代器"""
        if self.interface == "ollama":
            return self._chat_ollama(messages, stream=True, **kwargs)
        return self._chat_openai(messages, stream=True, **kwargs)

    # ---------- 健康检查 ----------
    def health_check(self) -> bool:
        """轻量探活：尝试一次极短请求"""
        try:
            resp = self.chat([{"role": "user", "content": "ping"}],
                             max_tokens=8, temperature=0.1)
            return bool(resp.text)
        except LLMAPIError:
            return False


def get_llm_adapter(cfg) -> Optional[LLMAdapter]:
    """根据 Config 创建 LLM 适配器；未配置 api_key 返回 None"""
    if not cfg.llm_enabled:
        return None
    return LLMAdapter(
        api_key=cfg.llm.api_key,
        base_url=cfg.llm.base_url,
        model_name=cfg.llm.model_name,
        interface_format=cfg.llm.interface_format,
        temperature=cfg.llm.temperature,
        max_tokens=cfg.llm.max_tokens,
        timeout=cfg.llm.timeout,
    )
