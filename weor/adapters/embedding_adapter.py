"""Embedding 适配器

用于 RAG 长篇一致性：把章节摘要向量化、按相似度召回历史上下文。
当前为轻量实现，仅做接口对齐；向量检索依赖 numpy / chromadb（可选依赖）。

若未安装可选依赖，相关方法会优雅返回空结果，不影响主流程。
"""
from __future__ import annotations

from typing import List, Optional
from dataclasses import dataclass

try:
    import requests
except ImportError as e:  # pragma: no cover
    raise ImportError("Embedding 适配器需要 requests") from e


@dataclass
class EmbeddingResult:
    text: str
    vector: List[float]
    metadata: dict


class EmbeddingAdapter:
    """向量化适配器（OpenAI 兼容 embeddings 接口）"""

    def __init__(self, api_key: str, base_url: str, model_name: str,
                 interface_format: str = "openai", timeout: int = 60):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model_name
        self.interface = interface_format
        self.timeout = timeout
        self._cache: dict = {}

    def embed(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        url = f"{self.base_url}/embeddings"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        payload = {"model": self.model, "input": texts}
        resp = requests.post(url, headers=headers, json=payload, timeout=self.timeout)
        if resp.status_code != 200:
            raise RuntimeError(f"Embedding 接口 {resp.status_code}: {resp.text[:200]}")
        data = resp.json()
        return [item["embedding"] for item in data["data"]]

    def embed_one(self, text: str) -> List[float]:
        if text in self._cache:
            return self._cache[text]
        vecs = self.embed([text])
        if vecs:
            self._cache[text] = vecs[0]
            return vecs[0]
        return []

    def cosine_similarity(self, a: List[float], b: List[float]) -> float:
        try:
            import numpy as np
            a, b = np.array(a), np.array(b)
            denom = (np.linalg.norm(a) * np.linalg.norm(b)) or 1.0
            return float(np.dot(a, b) / denom)
        except ImportError:
            # 纯 Python 兜底
            dot = sum(x * y for x, y in zip(a, b))
            na = sum(x * x for x in a) ** 0.5
            nb = sum(y * y for y in b) ** 0.5
            return dot / (na * nb) if na and nb else 0.0

    def retrieve(self, query: str, store: List[EmbeddingResult], k: int = 5
                 ) -> List[EmbeddingResult]:
        """从本地 store 中召回最相似的 k 条"""
        if not store or not query:
            return []
        qvec = self.embed_one(query)
        if not qvec:
            return []
        scored = [(self.cosine_similarity(qvec, r.vector), r) for r in store]
        scored.sort(key=lambda x: x[0], reverse=True)
        return [r for _, r in scored[:k]]


def get_embedding_adapter(cfg) -> Optional[EmbeddingAdapter]:
    """根据 Config 创建 Embedding 适配器；未配置 api_key 返回 None"""
    if not cfg.embedding.api_key:
        return None
    return EmbeddingAdapter(
        api_key=cfg.embedding.api_key,
        base_url=cfg.embedding.base_url,
        model_name=cfg.embedding.model_name,
        interface_format=cfg.embedding.interface_format,
    )
