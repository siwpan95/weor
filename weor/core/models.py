"""核心数据结构

提取并完善自原 autodugeon.py 的 dataclass。
所有引擎（离线/LLM）共用同一套数据结构，便于策略切换与结果统一处理。
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional


@dataclass
class Character:
    """小说角色"""
    name: str
    role: str = "supporting"          # protagonist | antagonist | supporting
    traits: List[str] = field(default_factory=list)
    motivation: str = ""
    background: str = ""
    current_emotion: str = "neutral"

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Scene:
    """小说场景"""
    location: str
    time: str
    characters: List[Character] = field(default_factory=list)
    action: str = ""
    description: str = ""
    emotional_tone: str = "neutral"
    conflict_level: int = 3           # 1-10

    def to_dict(self) -> dict:
        return {
            "location": self.location,
            "time": self.time,
            "characters": [c.to_dict() for c in self.characters],
            "action": self.action,
            "description": self.description,
            "emotional_tone": self.emotional_tone,
            "conflict_level": self.conflict_level,
        }


@dataclass
class Chapter:
    """小说章节"""
    number: int
    title: str
    scenes: List[Scene] = field(default_factory=list)
    summary: str = ""
    word_count: int = 0

    def to_dict(self) -> dict:
        return {
            "number": self.number,
            "title": self.title,
            "scenes": [s.to_dict() for s in self.scenes],
            "summary": self.summary,
            "word_count": self.word_count,
        }


@dataclass
class PlotPoint:
    """情节节点"""
    id: int
    type: str = "rising_action"       # inciting_incident | rising_action | climax | resolution
    description: str = ""
    characters_involved: List[str] = field(default_factory=list)
    location: str = ""
    importance: int = 5               # 1-10

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class NovelStructure:
    """小说结构（生成结果元数据，对应原 *_结构.json）"""
    title: str
    author: str = "weor engine"
    genre: str = "adventure"
    word_count: int = 0
    setting: Dict = field(default_factory=dict)
    plot_summary: str = ""
    characters: List[Character] = field(default_factory=list)
    chapters: List[Chapter] = field(default_factory=list)
    engine: str = "offline"           # offline | llm

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "author": self.author,
            "genre": self.genre,
            "word_count": self.word_count,
            "engine": self.engine,
            "setting": self.setting,
            "plot_summary": self.plot_summary,
            "characters": [c.to_dict() for c in self.characters],
            "chapters": [c.to_dict() for c in self.chapters],
        }
