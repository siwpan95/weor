"""生成流水线

编排整个小说生成流程：选择引擎 → 设定 → 大纲 → 章节 → 持久化。
这是对外的统一入口，屏蔽 offline / llm 引擎差异，并实现自动回落。

调用方式：
    from weor.core import Pipeline
    pipe = Pipeline(cfg)
    result = pipe.run(title="...", num_chapters=8, engine="auto")
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional, Tuple

from ..config import Config
from .models import NovelStructure
from .engine_offline import OfflineEngine
from .engine_llm import LLMEngine
from ..adapters.llm_adapter import get_llm_adapter, LLMAPIError


class PipelineResult:
    """流水线结果"""
    def __init__(self, structure: NovelStructure, text: str,
                 engine_used: str, output_path: Optional[Path] = None,
                 structure_path: Optional[Path] = None):
        self.structure = structure
        self.text = text
        self.engine_used = engine_used
        self.output_path = output_path
        self.structure_path = structure_path

    def __repr__(self) -> str:
        return (f"<PipelineResult title={self.structure.title!r} "
                f"engine={self.engine_used} words={self.structure.word_count}>")


class Pipeline:
    """生成流水线"""

    def __init__(self, cfg: Config):
        self.cfg = cfg

    def _select_engine(self, engine: str, genre: str, strategy: str):
        """选择引擎：auto 时优先 LLM，不可用则回落 offline"""
        if engine in ("llm", "auto"):
            adapter = get_llm_adapter(self.cfg)
            if adapter is not None:
                try:
                    return LLMEngine(adapter, genre=genre), "llm"
                except Exception:
                    pass  # 落到 offline
            if engine == "llm":
                raise RuntimeError(
                    "指定了 --engine llm 但未配置 LLM api_key，"
                    "请在 config.json 填入或改用 --engine auto/offline")
        # offline
        return OfflineEngine(genre=genre, strategy=strategy), "offline"

    def run(self, title: str = "无名之旅",
            num_chapters: int = 8,
            genre: Optional[str] = None,
            engine: str = "auto",
            strategy: str = "template",
            topic: str = "",
            words_per_chapter: int = 1500,
            save: bool = True) -> PipelineResult:
        """执行生成

        Args:
            title: 小说标题
            num_chapters: 章节数
            genre: 类型，None 时取 config.novel.genre
            engine: auto | llm | offline
            strategy: 离线策略 template|random|markov|nlp
            topic: 主题（LLM 引擎用）
            words_per_chapter: 每章字数目标
            save: 是否保存到 output/
        """
        genre = genre or self.cfg.novel.genre
        eng, engine_used = self._select_engine(engine, genre, strategy)

        # 真实 LLM 失败时自动回落
        try:
            structure, text = eng.generate_novel(
                title=title, num_chapters=num_chapters,
                topic=topic or self.cfg.novel.topic,
                words_per_chapter=words_per_chapter,
            )
        except (LLMAPIError, RuntimeError) as e:
            if engine_used == "llm":
                print(f"[weor] LLM 引擎失败（{e}），自动回落到离线引擎...")
                eng = OfflineEngine(genre=genre, strategy=strategy)
                engine_used = "offline (fallback)"
                structure, text = eng.generate_novel(
                    title=title, num_chapters=num_chapters,
                    topic=topic, words_per_chapter=words_per_chapter,
                )
            else:
                raise

        structure.engine = engine_used

        out_path = struct_path = None
        if save:
            out_path, struct_path = self._save(structure, text)
        return PipelineResult(structure, text, engine_used, out_path, struct_path)

    def _save(self, structure: NovelStructure, text: str
              ) -> tuple[Path, Path]:
        out_dir = Path(self.cfg.paths.output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        base = out_dir / structure.title
        txt_path = Path(f"{base}.txt")
        json_path = Path(f"{base}_结构.json")
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(text)
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(structure.to_dict(), f, ensure_ascii=False, indent=2)

        # 同步入库 library.db（小说表）
        try:
            from ..store.library import Library
            lib = Library(self.cfg.paths.library_db)
            lib.save_novel(structure.to_dict(), text)
        except Exception as e:
            # 入库失败不影响主流程
            print(f"[weor] 入库失败（不影响生成）：{e}")
        return txt_path, json_path
