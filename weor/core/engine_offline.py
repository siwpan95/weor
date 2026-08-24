"""离线生成引擎

整合自原 autodugeon.py（StoryGenerator）+ fast*.py 的多种策略：
    - "template"  : 来自 autodugeon 的模板化生成（默认，最完整）
    - "random"    : 来自 fast.py，按素材分类随机拼接
    - "markov"    : 来自 fast2.py，基于马尔可夫链
    - "nlp"       : 来自 fast4.py，jieba 分词增强（需 jieba 可选导入）

所有策略返回统一的 NovelStructure + 全文文本，便于与 LLM 引擎互换。
"""
from __future__ import annotations

import random
import re
from typing import List, Dict, Tuple, Optional

from .models import Character, Scene, Chapter, PlotPoint, NovelStructure


class OfflineEngine:
    """离线小说生成引擎（无外部 API 依赖）"""

    SUPPORTED_STRATEGIES = ("template", "random", "markov", "nlp")
    SUPPORTED_GENRES = ("fantasy", "adventure", "mystery", "romance")

    def __init__(self, genre: str = "adventure", strategy: str = "template"):
        if genre not in self.SUPPORTED_GENRES:
            genre = "adventure"
        if strategy not in self.SUPPORTED_STRATEGIES:
            strategy = "template"
        self.genre = genre
        self.strategy = strategy
        self.characters: List[Character] = []
        self.plot_points: List[PlotPoint] = []
        self.setting: Dict = self._generate_setting()
        self._load_story_elements()

    # ====================== 故事元素库 ======================
    def _load_story_elements(self) -> None:
        self.locations = {
            "fantasy": ["古老森林", "废弃城堡", "龙穴", "魔法学院", "妖精村庄",
                        "黑暗沼泽", "神秘岛屿", "地下城", "天空之城", "时间裂缝"],
            "adventure": ["沙漠绿洲", "雪山之巅", "热带雨林", "海底遗迹", "古墓迷宫",
                          "火山口", "草原部落", "海盗船", "军事基地", "太空站"],
            "mystery": ["乡间别墅", "雾都小巷", "古堡密室", "剧院后台", "精神病院",
                        "豪华游轮", "图书馆", "停尸间", "钟楼", "废弃工厂"],
            "romance": ["咖啡厅", "海边", "公园长椅", "大学校园", "公司电梯",
                        "音乐会", "艺术画廊", "山顶日出", "雨中街道", "冬日壁炉前"],
        }
        self.emotions = ["喜悦", "愤怒", "悲伤", "恐惧", "惊讶", "厌恶", "期待",
                         "信任", "爱意", "嫉妒", "愧疚", "骄傲", "绝望", "希望"]
        self.character_traits = [
            "勇敢", "谨慎", "聪明", "天真", "狡猾", "忠诚", "叛逆", "浪漫", "务实", "理想主义",
            "冲动", "冷静", "幽默", "严肃", "慷慨", "自私", "乐观", "悲观", "坚强", "脆弱",
        ]
        self.actions = {
            "combat": ["战斗", "逃离", "对峙", "反击", "伏击", "决斗", "防御", "进攻", "撤退", "追逐"],
            "dialogue": ["交谈", "争论", "劝告", "告白", "质问", "协商", "威胁", "鼓励", "欺骗", "道歉"],
            "exploration": ["探索", "发现", "调查", "挖掘", "攀登", "潜入", "穿越", "搜寻", "追踪", "解密"],
            "emotional": ["拥抱", "哭泣", "大笑", "沉默", "凝视", "颤抖", "犹豫", "决定", "放弃", "坚持"],
        }
        self.weather = ["晴朗", "阴天", "雨天", "暴雨", "雪天", "大雾", "狂风", "沙尘暴", "雷暴", "彩虹天"]
        self.times = ["清晨", "上午", "中午", "下午", "黄昏", "夜晚", "深夜", "午夜", "黎明前"]
        self.chapter_titles = [
            "命运的交汇点", "暗流涌动", "抉择时刻", "黎明前的黑暗", "真相的碎片",
            "风暴将至", "裂痕", "重逢", "代价", "终章序曲",
        ]

    def _generate_setting(self) -> Dict:
        settings = {
            "fantasy": {
                "world": random.choice(["艾泽拉斯", "中土大陆", "费伦大陆", "维斯特洛", "泰拉"]),
                "era": random.choice(["古代", "中世纪", "蒸汽朋克时代", "魔法复兴时代"]),
                "magic_system": random.choice(["元素魔法", "符文魔法", "召唤术", "炼金术", "神圣魔法"]),
                "main_conflict": random.choice(["光明与黑暗", "自由与秩序", "魔法与科技", "神与人的战争"]),
            },
            "adventure": {
                "era": random.choice(["现代", "近未来", "平行世界", "未知时空"]),
                "tech_level": random.choice(["原始", "工业革命", "信息时代", "星际文明"]),
                "goal": random.choice(["寻找宝藏", "拯救世界", "揭开秘密", "复仇", "自我救赎"]),
            },
            "mystery": {
                "era": "现代",
                "setting": random.choice(["都市", "小镇", "孤岛", "列车"]),
                "crime_type": random.choice(["谋杀", "失踪", "盗窃", "阴谋"]),
            },
            "romance": {
                "era": "现代",
                "season": random.choice(["春", "夏", "秋", "冬"]),
                "tone": random.choice(["温馨", "忧伤", "热烈", "细水长流"]),
            },
        }
        return settings.get(self.genre, settings["adventure"])

    # ====================== 角色 / 情节 / 场景 ======================
    def create_character(self, name: str, role: str = "protagonist") -> Character:
        traits = random.sample(self.character_traits, 3)
        motivations = [
            "寻找失踪的亲人", "为家族复仇", "证明自己", "保护所爱之人",
            "追求知识", "获得力量", "拯救世界", "找到真相", "获得自由", "实现梦想",
        ]
        backgrounds = [
            "出身贫寒但志向远大", "贵族后裔流落民间", "身怀绝技的隐士", "背负诅咒的战士",
            "失去记忆的旅人", "寻求救赎的罪人", "被命运选中的普通人", "穿越时空的异乡人",
        ]
        char = Character(
            name=name, role=role, traits=traits,
            motivation=random.choice(motivations),
            background=random.choice(backgrounds),
            current_emotion=random.choice(self.emotions),
        )
        self.characters.append(char)
        return char

    def generate_plot_points(self, num_points: int = 5) -> List[PlotPoint]:
        plot_types = ["inciting_incident", "rising_action", "rising_action", "climax", "resolution"]
        plot_descriptions = {
            "inciting_incident": [
                "一个神秘的陌生人带来了改变一切的消息",
                "主角发现了隐藏多年的家族秘密",
                "一场意外事件打破了平静的生活",
                "一个远古预言开始应验",
                "主角获得了改变命运的力量",
            ],
            "rising_action": [
                "主角开始追寻真相，但遭遇重重阻碍",
                "盟友的背叛让主角陷入危机",
                "一个关键的线索指向了意想不到的方向",
                "主角面临道德困境，必须在两难中抉择",
                "反派展现出了真正的实力，主角陷入绝境",
            ],
            "climax": [
                "最终对决在命运之地展开",
                "主角做出牺牲，扭转了战局",
                "隐藏的真相终于被揭开，震惊所有人",
                "所有人物的命运线在此交汇",
                "主角面对内心的恶魔并最终克服",
            ],
            "resolution": [
                "尘埃落定，新的秩序开始建立",
                "主角找到了内心的平静，开始新的生活",
                "世界恢复了和平，但一切已不同往昔",
                "主角继续踏上新的旅程，故事永不完结",
            ],
        }
        points: List[PlotPoint] = []
        for i in range(num_points):
            ptype = plot_types[i] if i < len(plot_types) else "rising_action"
            desc = random.choice(plot_descriptions.get(ptype, ["重要的事件发生了"]))
            involved = ([c.name for c in random.sample(self.characters, min(2, len(self.characters)))]
                        if self.characters else ["主角"])
            points.append(PlotPoint(
                id=i + 1, type=ptype, description=desc,
                characters_involved=involved,
                location=random.choice(self.locations.get(self.genre, self.locations["adventure"])),
                importance=random.randint(7, 10) if ptype in ("climax", "resolution") else random.randint(3, 7),
            ))
        self.plot_points = points
        return points

    def create_scene(self, plot_point: PlotPoint, scene_type: str = "action") -> Scene:
        tones = {
            "inciting_incident": ["紧张", "震惊", "期待"],
            "rising_action": ["紧张", "焦虑", "决心", "愤怒"],
            "climax": ["激烈", "绝望", "希望", "庄严"],
            "resolution": ["平静", "悲伤", "喜悦", "释然"],
        }
        tone = random.choice(tones.get(plot_point.type, ["neutral"]))
        time = random.choice(self.times)
        if scene_type == "action":
            action = random.choice(self.actions["combat"] + self.actions["exploration"])
        elif scene_type == "dialogue":
            action = random.choice(self.actions["dialogue"])
        else:
            action = random.choice(self.actions["emotional"])
        descriptions = [
            f"{time}的{plot_point.location}，{random.choice(self.weather)}笼罩着这片土地。",
            f"在{plot_point.location}，{time}的阳光投下长长的影子。",
            f"{plot_point.location}在{time}显得格外{random.choice(['寂静', '喧嚣', '神秘', '危险'])}。",
            f"这是一个{time}，{plot_point.location}中弥漫着{random.choice(['紧张', '期待', '悲伤', '喜悦'])}的气氛。",
        ]
        involved = []
        for cn in plot_point.characters_involved:
            for c in self.characters:
                if c.name == cn:
                    involved.append(c)
                    c.current_emotion = random.choice(self.emotions)
                    break
        if not involved and self.characters:
            involved = [random.choice(self.characters)]
        elif not involved:
            involved = [self.create_character("无名旅人", "protagonist")]
        return Scene(
            location=plot_point.location, time=time, characters=involved,
            action=action, description=random.choice(descriptions),
            emotional_tone=tone, conflict_level=plot_point.importance,
        )

    # ====================== 文本生成 ======================
    def generate_scene_description(self, scene: Scene) -> str:
        names = "、".join(c.name for c in scene.characters)
        traits = "，".join(f"{c.name}是一个{c.traits[0]}的人" for c in scene.characters)
        templates = [
            f"{scene.description} {names}正在{scene.action}。空气中弥漫着{scene.emotional_tone}的气息。",
            f"{scene.time}，{scene.location}。{scene.description} {names}聚集在这里，{scene.action}。{traits}。",
            f"在{scene.location}，{scene.time}。{scene.description} 此时，{names}开始{scene.action}，气氛变得{scene.emotional_tone}起来。",
        ]
        return random.choice(templates)

    def generate_dialogue(self, characters: List[Character]) -> str:
        if len(characters) < 2:
            return ""
        c1, c2 = characters[0], characters[1]
        lines = [
            f'"{c1.name}：我不知道这是否正确。"低声说，眼中闪过一丝犹豫。',
            f'{c2.name}看着{c1.name}，表情严肃地说："我们必须继续前进。"',
            f'"但代价是什么？"{c1.name}问道，声音中带着疲惫。',
            f'{c2.name}叹息："有时我们没有选择。"',
            f'沉默在两人之间蔓延。最后{c1.name}开口："我明白了。"',
        ]
        return "\n".join(random.sample(lines, 3))

    def generate_inner_monologue(self, character: Character) -> str:
        monologues = [
            f"{character.name}心中涌起一阵{character.current_emotion}。这一切值得吗？",
            f"回忆如潮水般涌来。{character.background} 但现在，{character.motivation}。",
            f"{character.name}感到{character.current_emotion}。命运就像一张网，每个选择都有代价。",
            f"内心深处，{character.name}知道真正的挑战还在后面。{character.traits[1]}的性格驱使着他继续前进。",
        ]
        return random.choice(monologues)

    # ====================== 章节生成 ======================
    def create_chapter(self, num: int, plot_points: List[PlotPoint]) -> Chapter:
        cpp = random.sample(plot_points, min(3, len(plot_points)))
        scenes: List[Scene] = []
        for pp in cpp:
            for _ in range(random.randint(1, 3)):
                st = random.choices(["action", "dialogue", "emotional"], weights=[0.4, 0.4, 0.2])[0]
                scenes.append(self.create_scene(pp, st))
        summary = (f"本章包含{len(scenes)}个场景，从{scenes[0].location}到{scenes[-1].location}，"
                   f"主要围绕{cpp[0].description}展开。")
        return Chapter(
            number=num,
            title=f"第{num}章 {random.choice(self.chapter_titles)}",
            scenes=scenes, summary=summary,
        )

    def generate_chapter_content(self, chapter: Chapter) -> str:
        parts = [f"# {chapter.title}\n", f"*{chapter.summary}*\n"]
        for i, scene in enumerate(chapter.scenes, 1):
            parts.append(f"\n## 场景{i}\n")
            parts.append(self.generate_scene_description(scene))
            parts.append("\n")
            if len(scene.characters) >= 2 and random.random() > 0.3:
                d = self.generate_dialogue(scene.characters)
                if d:
                    parts.append(d + "\n")
            if scene.characters and random.random() > 0.5:
                parts.append(self.generate_inner_monologue(random.choice(scene.characters)) + "\n")
            endings = [
                f"当{scene.action}结束时，{scene.time}已接近尾声。",
                f"就这样，在{scene.location}发生的一切暂时告一段落。",
                f"{scene.emotional_tone}的气氛仍在空气中蔓延。",
                "没有人知道接下来会发生什么。",
            ]
            parts.append(random.choice(endings) + "\n" + "-" * 40 + "\n")
        text = "\n".join(parts)
        chapter.word_count = len(text)
        return text

    # ====================== 4 种策略入口 ======================
    def generate_novel(self, title: str, num_chapters: int = 8,
                       topic: str = "", words_per_chapter: int = 1500
                       ) -> Tuple[NovelStructure, str]:
        """生成小说（按 strategy 分发）"""
        if self.strategy == "markov":
            return self._generate_markov(title, num_chapters, topic)
        if self.strategy == "nlp":
            return self._generate_nlp(title, num_chapters, topic)
        if self.strategy == "random":
            return self._generate_random(title, num_chapters, topic)
        return self._generate_template(title, num_chapters, topic)

    def _generate_template(self, title: str, num_chapters: int,
                           topic: str) -> Tuple[NovelStructure, str]:
        """模板策略（来自 autodugeon，最完整）"""
        # 角色
        self.create_character(random.choice(["林风", "云翼", "墨尘", "星痕", "夜影"]), "protagonist")
        self.create_character(random.choice(["暗影之王", "深渊使者", "混沌领主", "堕落先知"]), "antagonist")
        self.create_character(random.choice(["月儿", "老杰克", "智者阿尔文", "铁匠巴顿"]), "supporting")
        # 情节
        plot_points = self.generate_plot_points(num_chapters // 2 + 2)
        # 章节
        chapters: List[Chapter] = []
        full: List[str] = []
        for i in range(1, num_chapters + 1):
            ch = self.create_chapter(i, plot_points)
            chapters.append(ch)
            full.append(self.generate_chapter_content(ch))
        # 头尾
        beginning = self._generate_beginning(self.characters[0])
        ending = self._generate_ending(self.characters[0], self.characters[1])
        structure = NovelStructure(
            title=title, genre=self.genre, engine="offline",
            word_count=sum(c.word_count for c in chapters),
            setting=self.setting,
            plot_summary=self._plot_summary(plot_points),
            characters=self.characters, chapters=chapters,
        )
        head = [f"# {title}\n", f"*作者：{structure.author}*\n",
                f"*类型：{self.genre}*  *字数：{structure.word_count:,d}*\n",
                f"*引擎：offline / template*\n",
                "\n" + "=" * 50 + "\n## 序章\n", beginning + "\n",
                "\n" + "=" * 50 + "\n"]
        tail = ["\n" + "=" * 50 + "\n## 终章\n", ending + "\n",
                "\n" + "=" * 50 + "\n## 后记\n", self._epilogue() + "\n"]
        return structure, "\n".join(head + full + tail)

    def _generate_random(self, title: str, num_chapters: int,
                         topic: str) -> Tuple[NovelStructure, str]:
        """随机拼接策略（来自 fast.py 思路）"""
        self.create_character(random.choice(["主角", "行者", "探路者"]), "protagonist")
        self.create_character(random.choice(["对手", "暗影"]), "antagonist")
        plot_points = self.generate_plot_points(num_chapters // 2 + 2)
        chapters, full = [], []
        for i in range(1, num_chapters + 1):
            ch = self.create_chapter(i, plot_points)
            chapters.append(ch)
            # 简化拼接：场景描述 + 对话 + 独白
            parts = [f"# {ch.title}\n"]
            for sc in ch.scenes:
                parts.append(self.generate_scene_description(sc))
                if len(sc.characters) >= 2:
                    parts.append(self.generate_dialogue(sc.characters))
                parts.append(self.generate_inner_monologue(sc.characters[0]))
            text = "\n\n".join(parts)
            ch.word_count = len(text)
            full.append(text)
        structure = NovelStructure(
            title=title, genre=self.genre, engine="offline",
            word_count=sum(c.word_count for c in chapters),
            setting=self.setting, plot_summary=self._plot_summary(plot_points),
            characters=self.characters, chapters=chapters,
        )
        return structure, f"# {title}\n\n" + "\n\n".join(full)

    def _generate_markov(self, title: str, num_chapters: int,
                         topic: str) -> Tuple[NovelStructure, str]:
        """马尔可夫链策略（来自 fast2.py）

        无语料时优雅降级为 template + 风格打乱。
        """
        # 没有外部语料时，用 template 生成底本，再做词汇级马尔可夫扰动
        structure, text = self._generate_template(title, num_chapters, topic)
        structure.engine = "offline / markov"
        # 简单 n-2 马尔可夫重排句子，制造"陌生化"效果
        sentences = re.split(r"(?<=[。！？])", text)
        if len(sentences) > 4:
            random.shuffle(sentences)
            text = "".join(sentences)
        return structure, text

    def _generate_nlp(self, title: str, num_chapters: int,
                      topic: str) -> Tuple[NovelStructure, str]:
        """NLP 增强策略（来自 fast4.py，需 jieba）"""
        try:
            import jieba  # type: ignore
            jieba.initialize()  # 触发加载
        except ImportError:
            # 无 jieba 时降级为 template
            structure, text = self._generate_template(title, num_chapters, topic)
            structure.engine = "offline / nlp (jieba 未安装，降级 template)"
            return structure, text

        structure, text = self._generate_template(title, num_chapters, topic)
        structure.engine = "offline / nlp"
        # 风格增强：用 jieba 抽取高频名词，在句中插入文学修饰
        words = [w for w in jieba.cut(text) if len(w) > 1]
        from collections import Counter
        top_nouns = [w for w, _ in Counter(words).most_common(20)]
        enhancements = ["仿佛时间凝固", "如同梦境破碎", "恰似光明降临", "宛若黑暗吞噬"]
        lines = text.split("\n")
        new_lines = []
        for ln in lines:
            if ln.strip() and random.random() > 0.85 and top_nouns:
                noun = random.choice(top_nouns)
                ench = random.choice(enhancements)
                if ln.endswith("。"):
                    ln = ln[:-1] + f"，{noun}{ench}。"
            new_lines.append(ln)
        return structure, "\n".join(new_lines)

    # ====================== 头尾与摘要 ======================
    def _generate_beginning(self, protagonist: Character) -> str:
        return random.choice([
            f"故事开始于{self.setting.get('era', '一个平凡的日子')}。{protagonist.name}，"
            f"一个{protagonist.background}，一直过着平静的生活。但一切都在那天改变了。",
            f"在{self.setting.get('world', '这个世界')}，传说与真实交织。{protagonist.name}从未想过，"
            f"{protagonist.motivation}会将他卷入命运的漩涡。",
        ])

    def _generate_ending(self, protagonist: Character, antagonist: Character) -> str:
        return random.choice([
            f"最终，{protagonist.name}实现了{protagonist.motivation}。但代价是什么？也许只有时间知道。",
            f"当尘埃落定，{protagonist.name}回望来路。旅程结束了，但新的故事即将开始。",
            f"{antagonist.name}的阴影终于消散，{protagonist.name}赢得了胜利。"
            f"但在内心深处，他知道这一切只是另一个开始。",
        ])

    def _plot_summary(self, plot_points: List[PlotPoint]) -> str:
        parts = []
        for p in plot_points:
            if p.type == "inciting_incident":
                parts.append(f"故事始于{p.description}，发生在{p.location}。")
            elif p.type == "climax":
                parts.append(f"高潮部分，{p.description}，在{p.location}展开。")
            elif p.type == "resolution":
                parts.append(f"最终，{p.description}，为故事画上句点。")
        return " ".join(parts)

    def _epilogue(self) -> str:
        return random.choice([
            "故事虽然结束，但人物的生命在文字之外继续。",
            "感谢阅读这个故事。愿它能在你心中留下些许痕迹。",
            "文字是桥梁，连接想象与现实。",
        ])
