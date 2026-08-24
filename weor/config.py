"""weor 配置管理

加载 config.json（不存在则用默认值）。支持环境变量覆盖。
未配置 LLM api_key 时，引擎自动回落到离线生成。
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config.json"
EXAMPLE_CONFIG_PATH = PROJECT_ROOT / "config.example.json"


@dataclass
class LLMConfig:
    """LLM 适配器配置"""
    api_key: str = ""                       # 留空则回落到离线引擎
    base_url: str = "https://api.deepseek.com/v1"   # OpenAI 兼容端点
    model_name: str = "deepseek-chat"
    interface_format: str = "openai"       # openai | ollama
    temperature: float = 0.8
    max_tokens: int = 4096
    timeout: int = 60


@dataclass
class EmbeddingConfig:
    """向量化配置（用于 RAG 长篇一致性，可选）"""
    api_key: str = ""
    base_url: str = "https://api.deepseek.com/v1"
    model_name: str = "text-embedding-3-small"
    interface_format: str = "openai"
    retrieval_k: int = 5


@dataclass
class NovelConfig:
    """小说生成参数"""
    topic: str = "一场改变命运的冒险"
    genre: str = "adventure"               # adventure | fantasy | mystery | romance
    num_chapters: int = 8
    words_per_chapter: int = 1500
    style: str = "modern"                  # modern | classical | casual


@dataclass
class PathConfig:
    """路径配置"""
    data_dir: str = "data"
    output_dir: str = "output"
    library_db: str = "data/library.db"    # 统一素材库 + 小说库


@dataclass
class Config:
    """全局配置"""
    llm: LLMConfig = field(default_factory=LLMConfig)
    embedding: EmbeddingConfig = field(default_factory=EmbeddingConfig)
    novel: NovelConfig = field(default_factory=NovelConfig)
    paths: PathConfig = field(default_factory=PathConfig)

    @classmethod
    def load(cls, path: Optional[str] = None) -> "Config":
        """加载配置：优先环境变量 → config.json → 默认值"""
        cfg_path = Path(path) if path else DEFAULT_CONFIG_PATH
        cfg = cls()

        if cfg_path.exists():
            with open(cfg_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            for section in ("llm", "embedding", "novel", "paths"):
                if section in data:
                    sub = getattr(cfg, section)
                    for k, v in data[section].items():
                        if hasattr(sub, k):
                            setattr(sub, k, v)

        # 环境变量覆盖（优先级最高）
        env_key = os.environ.get("WEOR_LLM_API_KEY")
        if env_key:
            cfg.llm.api_key = env_key
        env_base = os.environ.get("WEOR_LLM_BASE_URL")
        if env_base:
            cfg.llm.base_url = env_base
        env_model = os.environ.get("WEOR_LLM_MODEL")
        if env_model:
            cfg.llm.model_name = env_model

        return cfg

    @property
    def llm_enabled(self) -> bool:
        """是否启用了 LLM（有 api_key 即视为启用）"""
        return bool(self.llm.api_key)

    def to_dict(self) -> dict:
        return asdict(self)

    def save(self, path: Optional[str] = None) -> None:
        """保存到 config.json"""
        cfg_path = Path(path) if path else DEFAULT_CONFIG_PATH
        with open(cfg_path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)


def ensure_example_config() -> None:
    """若 config.example.json 不存在则生成"""
    if not EXAMPLE_CONFIG_PATH.exists():
        Config().save(str(EXAMPLE_CONFIG_PATH))
