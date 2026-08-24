import random
import re

class TxtNovelGenerator:
    def __init__(self, material_files):
        """初始化，加载素材文件"""
        self.material = self._load_materials(material_files)
        
    def _load_materials(self, files):
        """从txt文件加载各种素材"""
        materials = {
            'characters': [],
            'locations': [],
            'actions': [],
            'dialogues': [],
            'descriptions': [],
            'plot_templates': []
        }
        
        # 遍历所有文件进行分类加载
        for file in files:
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    content = f.read().split('\n')
                    lines = [line.strip() for line in content if line.strip()]
                    
                    # 根据文件名智能分类存储
                    filename_lower = file.lower()
                    if 'character' in filename_lower or '人物' in filename_lower:
                        materials['characters'].extend(lines)
                    elif 'location' in filename_lower or '地点' in filename_lower:
                        materials['locations'].extend(lines)
                    elif 'action' in filename_lower or '动作' in filename_lower:
                        materials['actions'].extend(lines)
                    elif 'dialogue' in filename_lower or '对话' in filename_lower:
                        materials['dialogues'].extend(lines)
                    elif 'description' in filename_lower or '描写' in filename_lower:
                        materials['descriptions'].extend(lines)
                    elif 'template' in filename_lower or '模板' in filename_lower:
                        materials['plot_templates'].extend(lines)
                    else:
                        # 默认分类：按内容长度初步判断类型
                        for line in lines:
                            if len(line) > 20:
                                materials['descriptions'].append(line)
                            else:
                                materials['actions'].append(line)
            except FileNotFoundError:
                print(f"警告: 文件 {file} 未找到")
            except Exception as e:
                print(f"读取文件 {file} 时出错: {e}")
        
        return materials
    
    def _safe_choice(self, items, default=""):
        """安全选择，防止空列表"""
        if not items:
            return default
        return random.choice(items)
    
    def generate_sentence(self, template):
        """根据模板生成句子"""
        # 模板示例: "{character}在{location}{action}，{description}"
        sentence = template
        
        # 替换占位符 - 添加安全检查
        if '{character}' in sentence:
            char = self._safe_choice(self.material['characters'], "某人")
            sentence = sentence.replace('{character}', char)
        if '{character2}' in sentence:
            char2 = self._safe_choice(self.material['characters'], "另一个人")
            sentence = sentence.replace('{character2}', char2)
        if '{location}' in sentence:
            sentence = sentence.replace('{location}', self._safe_choice(self.material['locations'], "某处"))
        if '{action}' in sentence:
            sentence = sentence.replace('{action}', self._safe_choice(self.material['actions'], "行动"))
        if '{description}' in sentence:
            sentence = sentence.replace('{description}', self._safe_choice(self.material['descriptions'], "一切如常"))
        if '{dialogue}' in sentence:
            sentence = sentence.replace('{dialogue}', self._safe_choice(self.material['dialogues'], "..."))
            
        return sentence
    
    def generate_paragraph(self, num_sentences=5):
        """生成段落"""
        templates = [
            "{character}来到{location}。",
            "这里{description}。",
            "{character}{action}。",
            "突然，{description}。",
            "{character}心想：{dialogue}。",
            "{character2}对{character}说：{dialogue}",
            "此时，{location}{description}。"
        ]
        
        paragraph = []
        for _ in range(num_sentences):
            template = random.choice(templates)
            sentence = self.generate_sentence(template)
            paragraph.append(sentence)
            
        return ' '.join(paragraph)
    
    def generate_chapter(self, chapter_num, paragraphs=10, chapter_title=""):
        """生成章节"""
        chapter_header = f"第{chapter_num}章"
        if chapter_title:
            chapter_header += f" {chapter_title}"
        chapter = [chapter_header + "\n"]
        
        for i in range(paragraphs):
            paragraph = self.generate_paragraph(random.randint(3, 8))
            chapter.append(f"  {paragraph}\n\n")
            
        return '\n'.join(chapter)
    
    def generate_novel(self, num_chapters=5):
        """生成完整小说"""
        novel = ["=" * 50 + "\n", "自动生成小说\n", "=" * 50 + "\n\n"]
        
        for i in range(1, num_chapters + 1):
            chapter = self.generate_chapter(i, random.randint(8, 15))
            novel.append(chapter)
            novel.append("\n" + "=" * 50 + "\n\n")
            
        return ''.join(novel)