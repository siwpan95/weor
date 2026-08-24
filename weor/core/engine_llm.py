"""LLM 生成引擎

通过 LLM 适配器调用大模型，按"设定 → 大纲 → 章节 → 正文"自上而下流程生成小说。
参考行业最佳实践（AI_NovelGenerator / GOAT-Storytelling-Agent / Novel-OS）：
    - 分步生成，每步用结构化 prompt
    - 章节间维护全局摘要与角色状态，保证一致性
    - 不配置 api_key 时由 Pipeline 自动回落到 OfflineEngine

返回与 OfflineEngine 完全一致的 (NovelStructure, text)，可无缝互换。
"""
from __future__ import annotations

import json
import re
from typing import List, Dict, Tuple, Optional

from .models import Character, Scene, Chapter, PlotPoint, NovelStructure
from ..adapters.llm_adapter import LLMAdapter, LLMAPIError


SYSTEM_PROMPT = (
    "你是一位资深中文小说作者，擅长构建世界观、塑造立体角色、设计悬念与冲突。"
    "请严格按用户要求的格式输出，不要添加额外解释。"
)


class LLMEngine:
    """基于 LLM 的小说生成引擎"""

    def __init__(self, adapter: LLMAdapter, genre: str = "adventure"):
        self.adapter = adapter
        self.genre = genre
        self.characters: List[Character] = []
        self.global_summary: str = ""
        self.character_state: str = ""

    # ---------- 低层调用 ----------
    def _call(self, prompt: str, system: str = SYSTEM_PROMPT,
              max_tokens: int = 4096, temperature: float = 0.85) -> str:
        try:
            return self.adapter.generate(prompt, system=system,
                                          max_tokens=max_tokens,
                                          temperature=temperature)
        except LLMAPIError as e:
            raise RuntimeError(f"LLM 调用失败：{e}") from e

    @staticmethod
    def _strip_code_fence(text: str) -> str:
        """去掉 ```json ... ``` 之类的代码围栏"""
        m = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
        return (m.group(1) if m else text).strip()

    @staticmethod
    def _safe_json(text: str) -> dict:
        text = LLMEngine._strip_code_fence(text)
        # 截取第一个完整 JSON 对象
        start = text.find("{")
        if start < 0:
            return {}
        depth = 0
        for i in range(start, len(text)):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(text[start:i + 1])
                    except json.JSONDecodeError:
                        return {}
        return {}

    # ---------- 第 1 步：生成设定 ----------
    def generate_setting(self, topic: str) -> Dict:
        prompt = (
            f"为以下小说主题生成世界观设定，输出严格 JSON：\n"
            f"主题：{topic}\n类型：{self.genre}\n\n"
            f"JSON 格式：\n"
            '{{"era":"时代","world":"世界名","main_conflict":"核心冲突",'
            '"key_locations":["地点1","地点2","地点3"]}}\n'
            "只输出 JSON，不要解释。"
        )
        raw = self._call(prompt, max_tokens=600, temperature=0.8)
        data = self._safe_json(raw)
        if not data:
            data = {"era": "未知", "world": topic, "main_conflict": "命运的抉择",
                    "key_locations": ["起始之地", "试炼之场", "终焉之地"]}
        return data

    # ---------- 第 2 步：生成角色 ----------
    def generate_characters(self, topic: str, setting: Dict) -> List[Character]:
        prompt = (
            f"为小说生成 3 个核心角色，输出严格 JSON 数组：\n"
            f"主题：{topic}\n设定：{json.dumps(setting, ensure_ascii=False)}\n\n"
            "格式：\n"
            '[{"name":"名字","role":"protagonist|antagonist|supporting",'
            '"traits":["性格1","性格2","性格3"],"motivation":"动机",'
            '"background":"背景"}]\n只输出 JSON 数组。'
        )
        raw = self._call(prompt, max_tokens=800, temperature=0.85)
        raw = self._strip_code_fence(raw)
        # 尝试解析数组
        arr = []
        try:
            arr = json.loads(raw)
        except json.JSONDecodeError:
            m = re.search(r"\[.*\]", raw, re.DOTALL)
            if m:
                try:
                    arr = json.loads(m.group(0))
                except json.JSONDecodeError:
                    arr = []
        if not arr:
            arr = [
                {"name": "主角", "role": "protagonist", "traits": ["勇敢", "坚定", "聪明"],
                 "motivation": "完成使命", "background": "背负过去的旅人"},
                {"name": "对手", "role": "antagonist", "traits": ["冷酷", "智慧", "野心"],
                 "motivation": "夺取力量", "background": "失势的贵族"},
                {"name": "同伴", "role": "supporting", "traits": ["忠诚", "幽默", "谨慎"],
                 "motivation": "守护朋友", "background": "退役的战士"},
            ]
        chars = []
        for d in arr[:4]:
            chars.append(Character(
                name=d.get("name", "角色"),
                role=d.get("role", "supporting"),
                traits=d.get("traits", [])[:3] or ["未知"],
                motivation=d.get("motivation", "未知"),
                background=d.get("background", "未知"),
                current_emotion="neutral",
            ))
        self.characters = chars
        return chars

    # ---------- 第 3 步：生成大纲 ----------
    def generate_outline(self, topic: str, setting: Dict,
                         chars: List[Character], num_chapters: int) -> List[Dict]:
        char_desc = "\n".join(f"- {c.name}（{c.role}）：{c.motivation}；{c.background}"
                              for c in chars)
        prompt = (
            f"为小说生成 {num_chapters} 章的章节大纲，输出严格 JSON 数组：\n"
            f"主题：{topic}\n设定：{json.dumps(setting, ensure_ascii=False)}\n角色：\n{char_desc}\n\n"
            "格式：\n"
            '[{"number":1,"title":"章节标题","summary":"本章梗概(50-80字)",'
            '"key_events":["关键事件1","关键事件2"]}]'
            "\n要求：情节层层推进，有起承转合，只输出 JSON 数组。"
        )
        raw = self._call(prompt, max_tokens=1500, temperature=0.85)
        raw = self._strip_code_fence(raw)
        arr = []
        try:
            arr = json.loads(raw)
        except json.JSONDecodeError:
            m = re.search(r"\[.*\]", raw, re.DOTALL)
            if m:
                try:
                    arr = json.loads(m.group(0))
                except json.JSONDecodeError:
                    arr = []
        # 兜底
        if len(arr) < num_chapters:
            titles = ["启程", "初遇", "试炼", "转折", "暗流", "决战", "余波", "终章"]
            while len(arr) < num_chapters:
                idx = len(arr) + 1
                arr.append({"number": idx, "title": f"第{idx}章 {titles[idx % len(titles)]}",
                             "summary": f"第{idx}章的剧情发展。", "key_events": ["关键事件"]})
        return arr[:num_chapters]

    # ---------- 第 4 步：生成单章正文 ----------
    def generate_chapter_content(self, chapter_meta: Dict, chars: List[Character],
                                 setting: Dict, prev_summary: str) -> Tuple[str, str]:
        char_desc = "\n".join(f"- {c.name}（{c.role}）：动机={c.motivation}，性格={c.traits}"
                              for c in chars)
        prompt = (
            f"请撰写小说第 {chapter_meta['number']} 章正文，约 1200-1500 字。\n\n"
            f"章节标题：{chapter_meta['title']}\n"
            f"章节梗概：{chapter_meta['summary']}\n"
            f"关键事件：{', '.join(chapter_meta.get('key_events', []))}\n"
            f"世界观设定：{json.dumps(setting, ensure_ascii=False)}\n"
            f"角色：\n{char_desc}\n"
            f"前情摘要：{prev_summary or '（首章）'}\n\n"
            "要求：\n"
            "1. 文学性强，有场景描写、对话、内心独白\n"
            "2. 与前情保持一致，避免矛盾\n"
            "3. 章末留悬念\n"
            "4. 直接输出正文，不要标题前缀，不要解释\n\n"
            "正文结束后，另起一行用 === SUMMARY === 标记，再写 50 字以内的本章摘要，用于后续章节参考。"
        )
        raw = self._call(prompt, max_tokens=3000, temperature=0.9)
        # 拆分正文与摘要
        if "=== SUMMARY ===" in raw:
            body, _, summary = raw.partition("=== SUMMARY ===")
            return body.strip(), summary.strip()[:200]
        return raw.strip(), chapter_meta.get("summary", "")[:200]

    # ---------- 主入口 ----------
    def generate_novel(self, title: str, num_chapters: int = 8,
                       topic: str = "", words_per_chapter: int = 1500
                       ) -> Tuple[NovelStructure, str]:
        topic = topic or f"一场关于{title}的{self.genre}故事"

        # 1. 设定
        setting = self.generate_setting(topic)
        # 2. 角色
        chars = self.generate_characters(topic, setting)
        # 3. 大纲
        outline = self.generate_outline(topic, setting, chars, num_chapters)

        # 4. 逐章生成
        chapters: List[Chapter] = []
        full_parts: List[str] = [f"# {title}\n",
                                f"*类型：{self.genre} | 引擎：LLM | 章节数：{num_chapters}*\n",
                                "\n" + "=" * 50 + "\n"]
        running_summary = ""
        for ch_meta in outline:
            body, summary = self.generate_chapter_content(
                ch_meta, chars, setting, running_summary)
            running_summary = (running_summary + " " + summary).strip()
            chapter = Chapter(
                number=ch_meta["number"],
                title=ch_meta["title"],
                summary=summary,
                word_count=len(body),
            )
            chapters.append(chapter)
            full_parts.append(f"\n## {chapter.title}\n")
            full_parts.append(body + "\n")
            full_parts.append("\n" + "-" * 40 + "\n")

        # 5. 结构与全文
        structure = NovelStructure(
            title=title, genre=self.genre, engine="llm",
            word_count=sum(c.word_count for c in chapters),
            setting=setting,
            plot_summary=running_summary[:500],
            characters=chars, chapters=chapters,
        )
        full_parts.append("\n" + "=" * 50 + "\n## 后记\n由 weor LLM 引擎生成。\n")
        return structure, "\n".join(full_parts)
