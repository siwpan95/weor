"""
小说生成系统 - 基于探险日志生成连贯小说
无外部依赖，纯Python实现
"""

import random
import datetime
import json
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, asdict
import re

# ====================== 核心数据结构 ======================
@dataclass
class Character:
    """小说角色"""
    name: str
    role: str  # protagonist/antagonist/supporting
    traits: List[str]
    motivation: str
    background: str
    current_emotion: str = "neutral"
    
@dataclass
class Scene:
    """小说场景"""
    location: str
    time: str
    characters: List[Character]
    action: str
    description: str
    emotional_tone: str
    conflict_level: int  # 1-10
    
@dataclass
class Chapter:
    """小说章节"""
    title: str
    scenes: List[Scene]
    summary: str
    word_count: int = 0

@dataclass
class PlotPoint:
    """情节节点"""
    id: int
    type: str  # inciting_incident/rising_action/climax/resolution
    description: str
    characters_involved: List[str]
    location: str
    importance: int  # 1-10


# ====================== 故事生成器 ======================
class StoryGenerator:
    """故事生成引擎"""
    
    def __init__(self, genre: str = "adventure"):
        self.genre = genre
        self.characters = []
        self.plot_points = []
        self.scenes = []
        self.chapters = []
        self.setting = self._generate_setting()
        
        # 加载故事元素数据库
        self._load_story_elements()
        
    def _load_story_elements(self):
        """加载故事元素（内置于代码中）"""
        self.locations = {
            "fantasy": ["古老森林", "废弃城堡", "龙穴", "魔法学院", "妖精村庄", "黑暗沼泽", "神秘岛屿", "地下城", "天空之城", "时间裂缝"],
            "adventure": ["沙漠绿洲", "雪山之巅", "热带雨林", "海底遗迹", "古墓迷宫", "火山口", "草原部落", "海盗船", "军事基地", "太空站"],
            "mystery": ["乡间别墅", "雾都小巷", "古堡密室", "剧院后台", "精神病院", "豪华游轮", "图书馆", "停尸间", "钟楼", "废弃工厂"],
            "romance": ["咖啡厅", "海边", "公园长椅", "大学校园", "公司电梯", "音乐会", "艺术画廊", "山顶日出", "雨中街道", "冬日壁炉前"]
        }
        
        self.emotions = ["喜悦", "愤怒", "悲伤", "恐惧", "惊讶", "厌恶", "期待", "信任", "爱意", "嫉妒", "愧疚", "骄傲", "绝望", "希望"]
        
        self.character_traits = [
            "勇敢", "谨慎", "聪明", "天真", "狡猾", "忠诚", "叛逆", "浪漫", "务实", "理想主义",
            "冲动", "冷静", "幽默", "严肃", "慷慨", "自私", "乐观", "悲观", "坚强", "脆弱"
        ]
        
        self.actions = {
            "combat": ["战斗", "逃离", "对峙", "反击", "伏击", "决斗", "防御", "进攻", "撤退", "追逐"],
            "dialogue": ["交谈", "争论", "劝告", "告白", "质问", "协商", "威胁", "鼓励", "欺骗", "道歉"],
            "exploration": ["探索", "发现", "调查", "挖掘", "攀登", "潜入", "穿越", "搜寻", "追踪", "解密"],
            "emotional": ["拥抱", "哭泣", "大笑", "沉默", "凝视", "颤抖", "犹豫", "决定", "放弃", "坚持"]
        }
        
        self.weather = ["晴朗", "阴天", "雨天", "暴雨", "雪天", "大雾", "狂风", "沙尘暴", "雷暴", "彩虹天"]
        
        self.times = ["清晨", "上午", "中午", "下午", "黄昏", "夜晚", "深夜", "午夜", "黎明前"]
        
    def _generate_setting(self) -> Dict:
        """生成故事背景"""
        settings = {
            "fantasy": {
                "world": random.choice(["艾泽拉斯", "中土大陆", "费伦大陆", "维斯特洛", "泰拉"]),
                "era": random.choice(["古代", "中世纪", "蒸汽朋克时代", "魔法复兴时代"]),
                "magic_system": random.choice(["元素魔法", "符文魔法", "召唤术", "炼金术", "神圣魔法"]),
                "main_conflict": random.choice(["光明与黑暗", "自由与秩序", "魔法与科技", "神与人的战争"])
            },
            "adventure": {
                "era": random.choice(["现代", "近未来", "平行世界", "未知时空"]),
                "tech_level": random.choice(["原始", "工业革命", "信息时代", "星际文明"]),
                "goal": random.choice(["寻找宝藏", "拯救世界", "揭开秘密", "复仇", "自我救赎"])
            }
        }
        
        return settings.get(self.genre, settings["adventure"])
        
    def create_character(self, name: str, role: str = "protagonist") -> Character:
        """创建角色"""
        traits = random.sample(self.character_traits, 3)
        motivations = [
            "寻找失踪的亲人", "为家族复仇", "证明自己", "保护所爱之人", 
            "追求知识", "获得力量", "拯救世界", "找到真相", "获得自由", "实现梦想"
        ]
        backgrounds = [
            "出身贫寒但志向远大", "贵族后裔流落民间", "身怀绝技的隐士", "背负诅咒的战士",
            "失去记忆的旅人", "寻求救赎的罪人", "被命运选中的普通人", "穿越时空的异乡人"
        ]
        
        character = Character(
            name=name,
            role=role,
            traits=traits,
            motivation=random.choice(motivations),
            background=random.choice(backgrounds)
        )
        self.characters.append(character)
        return character
    
    def generate_plot_points(self, num_points: int = 5) -> List[PlotPoint]:
        """生成情节节点"""
        plot_types = ["inciting_incident", "rising_action", "rising_action", "climax", "resolution"]
        plot_descriptions = {
            "inciting_incident": [
                "一个神秘的陌生人带来了改变一切的消息",
                "主角发现了隐藏多年的家族秘密",
                "一场意外事件打破了平静的生活",
                "一个远古预言开始应验",
                "主角获得了改变命运的力量"
            ],
            "rising_action": [
                "主角开始追寻真相，但遭遇重重阻碍",
                "盟友的背叛让主角陷入危机",
                "一个关键的线索指向了意想不到的方向",
                "主角面临道德困境，必须在两难中抉择",
                "反派展现出了真正的实力，主角陷入绝境"
            ],
            "climax": [
                "最终对决在命运之地展开",
                "主角做出牺牲，扭转了战局",
                "隐藏的真相终于被揭开，震惊所有人",
                "所有人物的命运线在此交汇",
                "主角面对内心的恶魔并最终克服"
            ],
            "resolution": [
                "尘埃落定，新的秩序开始建立",
                "主角找到了内心的平静，开始新的生活",
                "世界恢复了和平，但一切已不同往昔",
                "主角继续踏上新的旅程，故事永不完结"
            ]
        }
        
        plot_points = []
        for i in range(num_points):
            plot_type = plot_types[i] if i < len(plot_types) else "rising_action"
            description = random.choice(plot_descriptions.get(plot_type, ["重要的事件发生了"]))
            
            # 选择涉及的角色
            if self.characters:
                involved = [char.name for char in random.sample(
                    self.characters, 
                    min(2, len(self.characters))
                )]
            else:
                involved = ["主角"]
            
            plot_point = PlotPoint(
                id=i+1,
                type=plot_type,
                description=description,
                characters_involved=involved,
                location=random.choice(self.locations.get(self.genre, self.locations["adventure"])),
                importance=random.randint(7, 10) if plot_type in ["climax", "resolution"] else random.randint(3, 7)
            )
            plot_points.append(plot_point)
            
        self.plot_points = plot_points
        return plot_points
    
    def create_scene(self, plot_point: PlotPoint, scene_type: str = "action") -> Scene:
        """创建场景"""
        # 确定情感基调
        emotional_tones = {
            "inciting_incident": ["紧张", "震惊", "期待"],
            "rising_action": ["紧张", "焦虑", "决心", "愤怒"],
            "climax": ["激烈", "绝望", "希望", "庄严"],
            "resolution": ["平静", "悲伤", "喜悦", "释然"]
        }
        
        tone = random.choice(emotional_tones.get(plot_point.type, ["neutral"]))
        
        # 选择时间
        time = random.choice(self.times)
        
        # 生成动作
        if scene_type == "action":
            action = random.choice(self.actions["combat"] + self.actions["exploration"])
        elif scene_type == "dialogue":
            action = random.choice(self.actions["dialogue"])
        else:
            action = random.choice(self.actions["emotional"])
        
        # 创建描述
        descriptions = [
            f"{time}的{plot_point.location}，{random.choice(self.weather)}笼罩着这片土地。",
            f"在{plot_point.location}，{time}的阳光（或阴影）投下长长的影子。",
            f"{plot_point.location}在{time}显得格外{random.choice(['寂静', '喧嚣', '神秘', '危险'])}。",
            f"这是一个{time}，{plot_point.location}中弥漫着{random.choice(['紧张', '期待', '悲伤', '喜悦'])}的气氛。"
        ]
        
        # 找到涉及的角色对象
        involved_chars = []
        for char_name in plot_point.characters_involved:
            for char in self.characters:
                if char.name == char_name:
                    involved_chars.append(char)
                    char.current_emotion = random.choice(self.emotions)
                    break
        
        # 如果没有找到角色，创建一个默认角色
        if not involved_chars and self.characters:
            involved_chars = [random.choice(self.characters)]
        elif not involved_chars:
            involved_chars = [self.create_character("无名旅人", "protagonist")]
        
        # 生成场景
        scene = Scene(
            location=plot_point.location,
            time=time,
            characters=involved_chars,
            action=action,
            description=random.choice(descriptions),
            emotional_tone=tone,
            conflict_level=plot_point.importance
        )
        
        return scene
    
    def generate_scene_description(self, scene: Scene) -> str:
        """生成场景的详细描述"""
        char_names = "、".join([char.name for char in scene.characters])
        char_traits = "，".join([f"{char.name}是一个{char.traits[0]}的人" for char in scene.characters])
        
        descriptions = [
            f"{scene.description} {char_names}正在{scene.action}。空气中弥漫着{scene.emotional_tone}的气息。",
            f"{scene.time}，{scene.location}。{scene.description} {char_names}聚集在这里，{scene.action}。{char_traits}。",
            f"在{scene.location}，{scene.time}。{scene.description} 此时，{char_names}开始{scene.action}，气氛变得{scene.emotional_tone}起来。"
        ]
        
        return random.choice(descriptions)
    
    def generate_dialogue(self, characters: List[Character]) -> str:
        """生成对话"""
        if len(characters) < 2:
            return ""
        
        char1, char2 = characters[0], characters[1]
        dialogues = [
            f'“我不知道这是否正确，”{char1.name}低声说，{random.choice(["眼中闪过一丝犹豫", "双手微微颤抖"])}。',
            f'{char2.name}看着{char1.name}，{random.choice(["表情严肃", "露出微笑", "眉头紧锁"])}地说：“我们必须继续前进。”',
            f'“但代价是什么？”{char1.name}问道，{random.choice(["声音中带着疲惫", "目光坚定"])}。',
            f'{char2.name}{random.choice(["叹息", "摇头", "握紧拳头"])}：“有时我们没有选择。”',
            f'沉默在两人之间蔓延。最后{char1.name}开口：“我明白了。{random.choice(["我会做的", "我们走", "就这样吧"])}。”'
        ]
        
        return "\n".join(random.sample(dialogues, 3))
    
    def generate_inner_monologue(self, character: Character) -> str:
        """生成内心独白"""
        monologues = [
            f"{character.name}心中涌起一阵{character.current_emotion}。{random.choice(['这一切值得吗？', '我是否走上了正确的道路？', '还有回头路吗？'])}",
            f"回忆如潮水般涌来。{character.background} 但现在，{character.motivation}",
            f"{character.name}感到{character.current_emotion}。{random.choice(['命运就像一张网', '每个选择都有代价', '有些路一旦走上就无法回头'])}",
            f"内心深处，{character.name}知道{random.choice(['这不会是结束', '真正的挑战还在后面', '必须坚持下去'])}。{character.traits[1]}的性格驱使着他继续前进。"
        ]
        
        return random.choice(monologues)
    
    def create_chapter(self, chapter_num: int, plot_points: List[PlotPoint]) -> Chapter:
        """创建章节"""
        # 为章节选择情节节点
        chapter_plot_points = random.sample(
            plot_points, 
            min(3, len(plot_points))
        )
        
        # 为每个情节节点创建场景
        chapter_scenes = []
        for plot_point in chapter_plot_points:
            # 决定场景类型
            scene_types = ["action", "dialogue", "emotional"]
            weights = [0.4, 0.4, 0.2]  # 动作和对话场景更常见
            
            for _ in range(random.randint(1, 3)):  # 每个情节点1-3个场景
                scene_type = random.choices(scene_types, weights=weights)[0]
                scene = self.create_scene(plot_point, scene_type)
                chapter_scenes.append(scene)
        
        # 生成章节标题
        chapter_titles = [
            f"第{chapter_num}章 命运的交汇点",
            f"第{chapter_num}章 暗流涌动",
            f"第{chapter_num}章 抉择时刻",
            f"第{chapter_num}章 黎明前的黑暗",
            f"第{chapter_num}章 真相的碎片"
        ]
        
        # 章节概要
        summary = f"本章包含{len(chapter_scenes)}个场景，从{chapter_scenes[0].location}到{chapter_scenes[-1].location}，" \
                 f"主要围绕{chapter_plot_points[0].description}展开。"
        
        chapter = Chapter(
            title=random.choice(chapter_titles),
            scenes=chapter_scenes,
            summary=summary
        )
        
        return chapter
    
    def generate_chapter_content(self, chapter: Chapter) -> str:
        """生成章节内容"""
        content = [f"# {chapter.title}\n"]
        content.append(f"*{chapter.summary}*\n")
        
        for i, scene in enumerate(chapter.scenes, 1):
            content.append(f"\n## 场景{i}\n")
            
            # 场景描述
            content.append(self.generate_scene_description(scene))
            content.append("\n")
            
            # 对话
            if len(scene.characters) >= 2 and random.random() > 0.3:
                dialogue = self.generate_dialogue(scene.characters)
                if dialogue:
                    content.append(dialogue)
                    content.append("\n")
            
            # 内心独白
            if scene.characters and random.random() > 0.5:
                pov_char = random.choice(scene.characters)
                monologue = self.generate_inner_monologue(pov_char)
                content.append(monologue)
                content.append("\n")
            
            # 场景结尾
            endings = [
                f"当{scene.action}结束时，{scene.time}已接近尾声。",
                f"就这样，在{scene.location}发生的一切暂时告一段落。",
                f"{scene.emotional_tone}的气氛仍在空气中蔓延。",
                f"没有人知道接下来会发生什么。"
            ]
            content.append(random.choice(endings))
            content.append("\n" + "-" * 40 + "\n")
        
        # 计算字数
        full_text = "\n".join(content)
        chapter.word_count = len(full_text)
        
        return full_text
    
    def generate_novel(self, title: str, num_chapters: int = 10) -> Dict:
        """生成完整小说"""
        print(f"开始生成小说：《{title}》")
        
        # 1. 创建角色
        print("创建角色...")
        protagonist = self.create_character(
            random.choice(["林风", "云翼", "墨尘", "星痕", "夜影"]), 
            "protagonist"
        )
        antagonist = self.create_character(
            random.choice(["暗影之王", "深渊使者", "混沌领主", "堕落先知"]), 
            "antagonist"
        )
        supporting = self.create_character(
            random.choice(["月儿", "老杰克", "智者阿尔文", "铁匠巴顿"]), 
            "supporting"
        )
        
        # 2. 生成情节
        print("构思情节...")
        plot_points = self.generate_plot_points(num_chapters // 2 + 2)
        
        # 3. 生成章节
        print(f"生成{num_chapters}个章节...")
        chapters = []
        full_novel = []
        
        for i in range(1, num_chapters + 1):
            print(f"  生成第{i}章...")
            chapter = self.create_chapter(i, plot_points)
            chapter_content = self.generate_chapter_content(chapter)
            
            chapters.append(chapter)
            full_novel.append(chapter_content)
        
        # 4. 生成开头和结尾
        print("撰写开头和结尾...")
        beginning = self._generate_beginning(protagonist)
        ending = self._generate_ending(protagonist, antagonist)
        
        # 5. 整合小说
        novel_structure = {
            "title": title,
            "author": "AI Storyteller",
            "genre": self.genre,
            "generated_date": datetime.datetime.now().strftime("%Y-%m-%d"),
            "word_count": sum(chapter.word_count for chapter in chapters),
            "chapters": chapters,
            "characters": self.characters,
            "setting": self.setting,
            "plot_summary": self._generate_plot_summary(plot_points)
        }
        
        # 完整文本
        full_text_parts = [
            f"# {title}\n",
            f"*作者：{novel_structure['author']}*\n",
            f"*类型：{self.genre}*  *字数：{novel_structure['word_count']:,d}*\n",
            f"*生成日期：{novel_structure['generated_date']}*\n",
            "\n" + "="*50 + "\n",
            "## 序章\n",
            beginning + "\n",
            "\n" + "="*50 + "\n"
        ]
        
        full_text_parts.extend(full_novel)
        
        full_text_parts.extend([
            "\n" + "="*50 + "\n",
            "## 终章\n",
            ending + "\n",
            "\n" + "="*50 + "\n",
            "## 后记\n",
            self._generate_epilogue() + "\n"
        ])
        
        full_text = "\n".join(full_text_parts)
        
        # 保存小说
        filename = f"{title}_小说.txt"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(full_text)
        
        # 保存结构信息
        with open(f"{title}_结构.json", "w", encoding="utf-8") as f:
            # 转换dataclass为字典
            json_data = {
                "title": novel_structure["title"],
                "author": novel_structure["author"],
                "genre": novel_structure["genre"],
                "word_count": novel_structure["word_count"],
                "setting": novel_structure["setting"],
                "plot_summary": novel_structure["plot_summary"],
                "characters": [asdict(char) for char in novel_structure["characters"]],
                "chapters": [
                    {
                        "title": chap.title,
                        "summary": chap.summary,
                        "scene_count": len(chap.scenes),
                        "word_count": chap.word_count
                    }
                    for chap in novel_structure["chapters"]
                ]
            }
            json.dump(json_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n小说生成完成！")
        print(f"标题：《{title}》")
        print(f"字数：{novel_structure['word_count']:,d}")
        print(f"章节数：{len(chapters)}")
        print(f"角色数：{len(self.characters)}")
        print(f"已保存为：{filename}")
        
        return novel_structure, full_text
    
    def _generate_beginning(self, protagonist: Character) -> str:
        """生成开头"""
        beginnings = [
            f"故事开始于{random.choice(self.setting.get('era', '一个平凡的日子'))}。{protagonist.name}，一个{protagonist.background}，一直过着{random.choice(['平静', '困苦', '迷茫'])}的生活。但一切都在那天改变了。",
            f"在{self.setting.get('world', '这个世界')}，传说与真实交织。{protagonist.name}从未想过，{protagonist.motivation}会将他卷入命运的漩涡。",
            f"风在{random.choice(self.locations[self.genre])}呼啸，{protagonist.name}站在这里，知道从今天起，一切都将不同。{protagonist.traits[0]}的他，即将踏上改变{random.choice(['自己', '世界', '所有人'])}命运的旅程。"
        ]
        
        return random.choice(beginnings)
    
    def _generate_ending(self, protagonist: Character, antagonist: Character) -> str:
        """生成结尾"""
        endings = [
            f"最终，{protagonist.name}实现了{protagonist.motivation}。但代价是什么？也许只有{random.choice(['风', '时间', '历史'])}知道。",
            f"当尘埃落定，{protagonist.name}站在{random.choice(self.locations[self.genre])}，{random.choice(['回望来路', '凝视远方', '低头沉思'])}。旅程结束了，但新的故事即将开始。",
            f"{antagonist.name}的阴影终于消散，{protagonist.name}赢得了{random.choice(['胜利', '和平', '救赎'])}。但在内心深处，他知道这一切只是另一个开始。"
        ]
        
        return random.choice(endings)
    
    def _generate_plot_summary(self, plot_points: List[PlotPoint]) -> str:
        """生成情节概要"""
        summary_parts = []
        for plot in plot_points:
            if plot.type == "inciting_incident":
                summary_parts.append(f"故事始于{plot.description}，发生在{plot.location}。")
            elif plot.type == "climax":
                summary_parts.append(f"高潮部分，{plot.description}，在{plot.location}展开。")
            elif plot.type == "resolution":
                summary_parts.append(f"最终，{plot.description}，为故事画上句点。")
        
        return " ".join(summary_parts)
    
    def _generate_epilogue(self) -> str:
        """生成后记"""
        epilogues = [
            "故事虽然结束，但人物的生命在文字之外继续。每个读者心中，都有一个属于自己的结局。",
            "感谢阅读这个故事。愿它能在你心中留下些许痕迹，如同微风拂过水面。",
            "文字是桥梁，连接想象与现实。愿这个故事曾带你短暂离开现实，进入另一个世界。"
        ]
        
        return random.choice(epilogues)


# ====================== 高级功能：风格模仿 ======================
class StyleEnhancer:
    """风格增强器 - 让文本更像小说"""
    
    def __init__(self):
        self.sentence_patterns = [
            "{adverb}，{subject} {verb} {object}。",
            "在{location}，{subject} {verb}着{object}。",
            "{time}，{subject} {emotion}地{verb}。",
            "{subject}的{body_part} {action}，仿佛{metaphor}。"
        ]
        
        self.adverbs = ["突然", "缓缓", "悄悄", "猛地", "轻轻", "迅速", "慢慢", "悄然"]
        self.verbs = ["看", "走", "跑", "跳", "说", "想", "感受", "回忆", "挣扎", "决定"]
        self.emotions = ["悲伤", "喜悦", "愤怒", "恐惧", "平静", "激动", "迷茫", "坚定"]
        self.body_parts = ["手", "眼睛", "心", "脚步", "呼吸", "声音", "背影", "思绪"]
        self.metaphors = ["时间凝固", "世界静止", "梦境破碎", "希望重生", "光明降临", "黑暗吞噬"]
        
    def enhance_sentence(self, sentence: str) -> str:
        """增强句子文学性"""
        # 简单的文本增强
        enhancements = [
            (r"(\w+)说", r"\1低声说道"),
            (r"(\w+)走", r"\1缓缓走去"),
            (r"(\w+)看", r"\1凝视着"),
            (r"(\w+)想", r"\1思索着"),
            (r"然后", r"接着"),
            (r"但是", r"然而"),
            (r"所以", r"因此"),
            (r"很(\w+)", r"十分\1"),
        ]
        
        for pattern, replacement in enhancements:
            sentence = re.sub(pattern, replacement, sentence)
        
        # 随机添加文学描写
        if random.random() > 0.7:
            literary_additions = [
                "，风轻轻吹过。",
                "，月光洒在地上。",
                "，空气中弥漫着莫名的气息。",
                "，时间仿佛在此刻停滞。"
            ]
            if sentence[-1] in "。！？":
                sentence = sentence[:-1] + random.choice(literary_additions) + sentence[-1]
        
        return sentence
    
    def generate_literary_description(self, subject: str, action: str) -> str:
        """生成文学性描述"""
        pattern = random.choice(self.sentence_patterns)
        
        description = pattern.format(
            adverb=random.choice(self.adverbs),
            subject=subject,
            verb=action + random.choice(["", "了", "着"]),
            object=random.choice(["远方", "前方", "一切", "这个世界"]),
            location=random.choice(["这里", "那里", "此处", "彼方"]),
            time=random.choice(["此刻", "那时", "这时", "一瞬间"]),
            emotion=random.choice(self.emotions),
            body_part=random.choice(self.body_parts),
            action=random.choice(["颤抖", "凝固", "加速", "停滞"]),
            metaphor=random.choice(self.metaphors)
        )
        
        return self.enhance_sentence(description)


# ====================== 探险日志转小说转换器 ======================
class AdventureLogToNovelConverter:
    """将探险日志转换为小说"""
    
    def __init__(self, log_file: str):
        self.log_file = log_file
        self.logs = self._load_logs()
        self.story_generator = StoryGenerator("adventure")
        
    def _load_logs(self) -> List[str]:
        """加载日志文件"""
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                return f.readlines()
        except:
            # 如果文件不存在，使用示例日志
            return [
                "第1天: 天气晴朗，向北方探索，发现野果丛",
                "第2天: 下雨，在森林中扎营，遭遇野兽",
                "第3天: 大雾，向东方前进，找到古代遗迹",
                "第5天: 暴风雨，在洞穴躲避，发现神秘壁画",
                "第8天: 晴朗，穿越沙漠，几乎渴死但找到绿洲",
                "第12天: 阴天，与队友争吵，分道扬镳",
                "第15天: 发现宝藏，但触发了陷阱",
                "第20天: 与最终敌人对决，险胜但重伤",
                "第25天: 返回起点，但一切都已改变"
            ]
    
    def extract_plot_from_logs(self) -> List[Dict]:
        """从日志中提取情节"""
        plot_points = []
        
        for i, log in enumerate(self.logs):
            if i % 3 == 0:  # 每3条日志作为一个情节点
                plot_type = "inciting_incident" if i == 0 else "rising_action"
                if i == len(self.logs) - 3:
                    plot_type = "climax"
                elif i >= len(self.logs) - 1:
                    plot_type = "resolution"
                
                # 从日志中提取关键词
                if "发现" in log or "找到" in log:
                    description = f"发现了重要的线索或物品：{log.strip()}"
                elif "遭遇" in log or "战斗" in log or "对决" in log:
                    description = f"遭遇了危险或敌人：{log.strip()}"
                elif "死亡" in log or "渴死" in log or "重伤" in log:
                    description = f"面临生死危机：{log.strip()}"
                elif "返回" in log or "结束" in log or "完成" in log:
                    description = f"旅程的终结：{log.strip()}"
                else:
                    description = f"探险中的事件：{log.strip()}"
                
                plot_points.append({
                    "id": i + 1,
                    "type": plot_type,
                    "description": description,
                    "importance": min(10, 3 + i // 2)  # 越往后越重要
                })
        
        return plot_points
    
    def convert_to_novel(self, title: str = "探险日志") -> str:
        """将日志转换为小说"""
        print(f"正在将探险日志转换为小说：《{title}》")
        
        # 从日志中提取情节
        log_plots = self.extract_plot_from_logs()
        
        # 创建基于日志的角色
        protagonist = self.story_generator.create_character(
            random.choice(["探险家", "冒险者", "旅人", "寻宝者"]),
            "protagonist"
        )
        
        # 如果有足够的日志，创建更多角色
        if len(self.logs) > 5:
            companion = self.story_generator.create_character(
                random.choice(["向导", "队友", "学者", "战士"]),
                "supporting"
            )
        
        if len(self.logs) > 10:
            enemy = self.story_generator.create_character(
                random.choice(["守护者", "怪物", "对手", "神秘人"]),
                "antagonist"
            )
        
        # 基于日志生成自定义情节
        plot_points = []
        for i, plot_data in enumerate(log_plots):
            plot_point = PlotPoint(
                id=plot_data["id"],
                type=plot_data["type"],
                description=plot_data["description"],
                characters_involved=[protagonist.name],
                location=random.choice(self.story_generator.locations["adventure"]),
                importance=plot_data["importance"]
            )
            plot_points.append(plot_point)
        
        self.story_generator.plot_points = plot_points
        
        # 生成小说
        novel_structure, novel_text = self.story_generator.generate_novel(
            title=title,
            num_chapters=min(10, max(3, len(self.logs) // 3))
        )
        
        # 添加基于日志的特殊章节
        log_chapter = self._create_log_based_chapter()
        novel_text += "\n\n" + log_chapter
        
        return novel_text
    
    def _create_log_based_chapter(self) -> str:
        """创建基于日志的特别章节"""
        chapter = ["\n" + "="*50, "## 日志记录", "="*50 + "\n"]
        chapter.append("以下是根据原始探险日志整理的关键记录：\n")
        
        for i, log in enumerate(self.logs):
            if i < 20:  # 只显示前20条
                chapter.append(f"**第{i+1}条记录**：{log.strip()}")
        
        chapter.append("\n> *这些简单的记录背后，是一个个生死瞬间，一次次艰难抉择。*")
        
        return "\n".join(chapter)


# ====================== 主程序 ======================
def main():
    """主程序"""
    print("小说生成系统")
    print("="*50)
    print("1. 生成随机小说")
    print("2. 从探险日志生成小说")
    print("3. 自定义生成")
    print("4. 退出")
    
    while True:
        choice = input("\n请选择 (1-4): ").strip()
        
        if choice == "1":
            # 随机生成小说
            genre = input("选择类型 (1.冒险 2.奇幻 3.悬疑 4.爱情): ").strip()
            genres = {"1": "adventure", "2": "fantasy", "3": "mystery", "4": "romance"}
            selected_genre = genres.get(genre, "adventure")
            
            title = input("小说标题 (默认: 无名之旅): ").strip() or "无名之旅"
            chapters = input("章节数 (默认: 8): ").strip()
            chapters = int(chapters) if chapters.isdigit() else 8
            
            generator = StoryGenerator(selected_genre)
            generator.generate_novel(title, chapters)
            
        elif choice == "2":
            # 从日志生成小说
            log_file = input("日志文件路径 (直接回车使用示例): ").strip()
            title = input("小说标题 (默认: 探险日志改编): ").strip() or "探险日志改编"
            
            converter = AdventureLogToNovelConverter(log_file if log_file else "")
            novel = converter.convert_to_novel(title)
            
            # 保存
            filename = f"{title}_日志改编.txt"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(novel)
            print(f"\n已保存为: {filename}")
            
        elif choice == "3":
            # 自定义生成
            print("\n自定义生成选项:")
            print("1. 增强文学性")
            print("2. 生成对话片段")
            print("3. 生成场景描述")
            
            sub_choice = input("请选择: ").strip()
            
            if sub_choice == "1":
                text = input("输入要增强的文本: ").strip()
                enhancer = StyleEnhancer()
                enhanced = enhancer.enhance_sentence(text)
                print(f"增强后: {enhanced}")
                
            elif sub_choice == "2":
                char1 = input("角色1: ").strip() or "张三"
                char2 = input("角色2: ").strip() or "李四"
                
                generator = StoryGenerator()
                char_a = generator.create_character(char1, "protagonist")
                char_b = generator.create_character(char2, "supporting")
                
                dialogue = generator.generate_dialogue([char_a, char_b])
                print("\n生成的对话:")
                print(dialogue)
                
            elif sub_choice == "3":
                location = input("场景地点: ").strip() or "森林"
                time = input("时间: ").strip() or "黄昏"
                character = input("角色名: ").strip() or "旅人"
                action = input("动作: ").strip() or "行走"
                
                generator = StoryGenerator()
                char = generator.create_character(character)
                scene = Scene(
                    location=location,
                    time=time,
                    characters=[char],
                    action=action,
                    description=f"{time}的{location}",
                    emotional_tone="平静",
                    conflict_level=3
                )
                
                description = generator.generate_scene_description(scene)
                print("\n生成的场景描述:")
                print(description)
        
        elif choice == "4":
            print("再见！")
            break
            
        else:
            print("无效选择，请重试")


def quick_demo():
    """快速演示"""
    print("\n快速演示：生成一个短篇冒险小说")
    print("="*50)
    
    # 快速生成
    generator = StoryGenerator("adventure")
    novel_structure, novel_text = generator.generate_novel("秘境追踪", 5)
    
    # 显示片段
    lines = novel_text.split('\n')
    print("\n=== 小说开头 ===")
    for i in range(min(20, len(lines))):
        print(lines[i])
    
    print("\n...\n")
    
    print("=== 小说结尾 ===")
    for i in range(max(0, len(lines)-10), len(lines)):
        print(lines[i])
    
    print(f"\n小说已生成完毕！共{novel_structure['word_count']:,d}字")


# ====================== 示例：从探险游戏生成小说 ======================
def generate_novel_from_adventure_game(logs: List[str], title: str = "探险传奇") -> str:
    """从游戏日志生成小说（整合函数）"""
    # 将日志保存为临时文件
    temp_file = "temp_adventure_log.txt"
    with open(temp_file, "w", encoding="utf-8") as f:
        f.write("\n".join(logs))
    
    # 转换为小说
    converter = AdventureLogToNovelConverter(temp_file)
    novel = converter.convert_to_novel(title)
    
    return novel


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--demo":
        quick_demo()
    else:
        main()