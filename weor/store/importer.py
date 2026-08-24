"""素材导入器

重写自原 content_import_tool.py（源文件已丢失，根据 dist/wri.txt 的标签格式重建）。
支持两种格式：
    1. 标签格式（来自 wri.txt）：以 #characters/#scenes/#dialogues/#descriptions/#plots/#styles 标记行
    2. 自由文本：按文件名关键词分类（character/人物 → characters，location/地点 → scenes...）

导入后写入 Library.materials 表。
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import List, Dict, Tuple

from .library import Library


# 标签 → category 映射
TAG_MAP = {
    "characters": "characters",
    "character": "characters",
    "人物": "characters",
    "scenes": "scenes",
    "scene": "scenes",
    "场景": "scenes",
    "地点": "scenes",
    "dialogues": "dialogues",
    "dialogue": "dialogues",
    "对话": "dialogues",
    "descriptions": "descriptions",
    "description": "descriptions",
    "描写": "descriptions",
    "plots": "plots",
    "plot": "plots",
    "情节": "plots",
    "styles": "styles",
    "style": "styles",
    "风格": "styles",
}


class MaterialImporter:
    """素材导入器"""

    def __init__(self, library: Library):
        self.library = library

    # ---------- 标签格式解析 ----------
    @staticmethod
    def parse_tagged(text: str) -> List[Tuple[str, str]]:
        """解析 wri.txt 风格的标签格式

        格式：每行 #tag content，后续非 # 行归入当前 tag。
        多个 #tag 可叠加（如同时有 #scenes 多行）。
        """
        entries: List[Tuple[str, str]] = []
        current_tags: List[str] = []
        for line in text.splitlines():
            line = line.rstrip()
            if not line.strip():
                continue
            m = re.match(r"^#(\w+)\s+(.*)$", line)
            if m:
                tag_raw = m.group(1).lower()
                content = m.group(2).strip()
                # 一个 # 行可能属于多个 tag（如 "#characters 艾莉娅" 后跟 "#scenes ..."）
                cat = TAG_MAP.get(tag_raw)
                if cat:
                    current_tags = [cat]
                    if content:
                        entries.append((cat, content))
                continue
            # 非 # 行：追加到当前所有 tag
            if current_tags and line.strip():
                for t in current_tags:
                    entries.append((t, line.strip()))
        return entries

    # ---------- 文件名分类 ----------
    @staticmethod
    def classify_by_name(filename: str, line: str) -> str:
        fn = filename.lower()
        if "character" in fn or "人物" in fn:
            return "characters"
        if "location" in fn or "地点" in fn:
            return "scenes"
        if "dialogue" in fn or "对话" in fn:
            return "dialogues"
        if "description" in fn or "描写" in fn:
            return "descriptions"
        if "plot" in fn or "情节" in fn:
            return "plots"
        if "style" in fn or "风格" in fn:
            return "styles"
        # 按内容长度兜底
        return "descriptions" if len(line) > 20 else "actions"

    # ---------- 导入入口 ----------
    def import_file(self, file_path: str, source: str = "imported") -> int:
        """导入单个 txt 文件，返回导入条数"""
        p = Path(file_path)
        if not p.exists():
            raise FileNotFoundError(f"素材文件不存在：{file_path}")
        text = p.read_text(encoding="utf-8")
        fname = p.name

        # 优先按标签格式解析
        entries = self.parse_tagged(text)
        if not entries:
            # 退化为按文件名 + 行分类
            for line in text.splitlines():
                line = line.strip()
                if line:
                    cat = self.classify_by_name(fname, line)
                    entries.append((cat, line))

        count = 0
        for cat, content in entries:
            if content:
                self.library.add_material(content=content, category=cat,
                                          source=source, tags=[fname])
                count += 1
        return count

    def import_directory(self, dir_path: str) -> Dict[str, int]:
        """批量导入目录下所有 txt，返回 {文件名: 导入条数}"""
        d = Path(dir_path)
        if not d.exists() or not d.is_dir():
            raise FileNotFoundError(f"目录不存在：{dir_path}")
        result: Dict[str, int] = {}
        for txt in sorted(d.glob("*.txt")):
            try:
                result[txt.name] = self.import_file(str(txt))
            except Exception as e:
                result[txt.name] = -1
                print(f"[weor] 导入 {txt.name} 失败：{e}")
        return result

    def import_export_json(self, json_path: str) -> int:
        """从原 export.json 导入（兼容旧格式）"""
        import json
        p = Path(json_path)
        if not p.exists():
            raise FileNotFoundError(f"export.json 不存在：{json_path}")
        data = json.loads(p.read_text(encoding="utf-8"))
        count = 0
        for item in data:
            cat = item.get("content_type") or item.get("category") or "descriptions"
            self.library.add_material(
                content=item.get("content", ""),
                category=cat,
                tags=item.get("tags", []),
                source=item.get("source", "exported"),
                weight=item.get("weight", 1.0),
                metadata=item.get("metadata", {}),
            )
            count += 1
        return count
