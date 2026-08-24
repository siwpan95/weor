# 结合简单NLP提升质量
import re
import random
import jieba  # 中文分词
from collections import Counter

class EnhancedGenerator:
    def __init__(self):
        """初始化增强生成器"""
        self.corpus_data = None
        self.word_freq = Counter()
        self.sentence_patterns = []
        
    def analyze_corpus(self, txt_file):
        """分析语料库特征"""
        try:
            with open(txt_file, 'r', encoding='utf-8') as f:
                text = f.read()
        except FileNotFoundError:
            raise FileNotFoundError(f"语料文件 {txt_file} 未找到")
        except Exception as e:
            raise Exception(f"读取语料文件失败: {e}")
        
        # 分词分析
        words = list(jieba.cut(text))
        # 过滤停用词和单字
        filtered_words = [w for w in words if len(w) > 1 and w.strip() not in ['的', '了', '是', '在', '和', '有', '我', '他', '她', '它', '们']]
        self.word_freq = Counter(filtered_words)
        
        # 提取常用句式
        sentences = re.split(r'[。！？]', text)
        self.sentence_patterns = []
        
        for sent in sentences:
            sent = sent.strip()
            if len(sent) > 4:  # 过滤短句
                # 提取句式模式：保留主语、动词、宾语结构
                pattern = self._extract_pattern(sent)
                if pattern:
                    self.sentence_patterns.append(pattern)
        
        # 计算平均句子长度
        valid_sentences = [s for s in sentences if len(s.strip()) > 4]
        avg_len = sum(len(s) for s in valid_sentences) / max(len(valid_sentences), 1)
        
        # 存储分析结果
        self.corpus_data = {
            'common_words': self.word_freq.most_common(50),
            'sentence_patterns': self.sentence_patterns[:20],
            'avg_sentence_len': avg_len,
            'total_chars': len(text),
            'total_sentences': len(valid_sentences)
        }
        
        return self.corpus_data
    
    def _extract_pattern(self, sentence):
        """提取句子结构模式"""
        # 简单模式：识别"[角色][动作][对象]"结构
        words = list(jieba.cut(sentence))
        
        # 定义常见的动作词性（简化处理）
        action_keywords = ['来到', '发现', '看到', '听到', '说道', '走进', '离开', '停下', '转身', '抬头']
        
        pattern_parts = []
        for i, word in enumerate(words):
            if any(action in word for action in action_keywords):
                pattern_parts.append('[动作]')
            elif i < len(words) - 1 and any(action in words[i+1] for action in action_keywords):
                pattern_parts.append('[角色]')
        
        if pattern_parts:
            return ''.join(pattern_parts[:5])  # 限制模式长度
        return sentence[:15] + "..." if len(sentence) > 15 else sentence
    
    def _get_safe_choice(self, items, default=""):
        """安全选择，防止空列表"""
        if not items:
            return default
        return random.choice(items)
    
    def generate_enhanced_text(self, length=100, seed_words=None):
        """基于分析结果生成增强文本"""
        if not self.corpus_data:
            raise ValueError("请先调用 analyze_corpus 方法分析语料库")
        
        # 基于高频词生成
        top_words = [w for w, _ in self.word_freq.most_common(20)]
        
        if seed_words is None:
            # 随机选择一些高频词作为种子
            seed_words = random.sample(top_words, min(3, len(top_words)))
        
        result = []
        current_pos = 0
        
        for _ in range(length):
            if current_pos < len(self.sentence_patterns):
                # 使用提取的句式模式
                pattern = self._get_safe_choice(self.sentence_patterns, "[角色][动作]")
                # 用高频词填充
                filled = pattern.replace('[角色]', self._get_safe_choice(top_words, '某人'))
                filled = filled.replace('[动作]', self._get_safe_choice(top_words, '行动'))
                result.append(filled)
            else:
                # 使用高频词组合
                words = [self._get_safe_choice(list(self.word_freq.keys()), '某') for _ in range(5)]
                result.append(''.join(words))
            current_pos += 1
        
        return ' '.join(result)
    
    def get_word_analysis(self, top_n=20):
        """获取词频分析结果"""
        if not self.corpus_data:
            return None
        
        # 计算总词数
        total_words = sum(count for word, count in self.corpus_data['common_words'])
        
        return {
            'top_words': self.corpus_data['common_words'][:top_n],
            'avg_length': self.corpus_data['avg_sentence_len'],
            'total_words': total_words
        }