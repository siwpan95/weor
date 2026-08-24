import collections
import random
import re

class MarkovNovelGenerator:
    def __init__(self, corpus_file, order=2):
        """基于马尔可夫链的生成器"""
        try:
            with open(corpus_file, 'r', encoding='utf-8') as f:
                self.text = f.read()
        except FileNotFoundError:
            raise FileNotFoundError(f"语料文件 {corpus_file} 未找到")
        except Exception as e:
            raise Exception(f"读取语料文件失败: {e}")
        
        if not self.text.strip():
            raise ValueError("语料文件为空")
        
        self.order = order  # 马尔可夫链阶数
        self.markov_chain = self._build_chain()
        self.words = self._tokenize()
    
    def _tokenize(self):
        """分词处理"""
        # 使用正则表达式分词，保留标点符号
        words = re.findall(r'\w+|[^\w\s]', self.text)
        return words
    
    def _build_chain(self):
        """构建马尔可夫链"""
        chain = collections.defaultdict(list)
        words = self.words
        
        for i in range(len(words) - self.order):
            key = tuple(words[i:i + self.order])
            value = words[i + self.order]
            chain[key].append(value)
            
        if not chain:
            raise ValueError("语料库太小，无法构建马尔可夫链")
            
        return chain
    
    def _get_valid_starts(self):
        """获取所有有效的起始词序列"""
        # 选择以句号、问号、感叹号开头的序列作为句子开头
        valid_starts = []
        for i in range(len(self.words) - self.order):
            if self.words[i] in '。！？':
                valid_starts.append(tuple(self.words[i+1:i + self.order + 1]))
        return valid_starts if valid_starts else list(self.markov_chain.keys())
    
    def generate_text(self, length=100, seed=None):
        """生成文本"""
        if seed is None:
            # 优先从句子开头选择
            valid_starts = self._get_valid_starts()
            if valid_starts:
                words = list(random.choice(valid_starts))
            else:
                start_idx = random.randint(0, len(self.words) - self.order)
                words = self.words[start_idx:start_idx + self.order]
        else:
            words = seed.split()[:self.order]
        
        result = list(words)
        
        for _ in range(length):
            key = tuple(result[-self.order:])
            if key in self.markov_chain:
                next_word = random.choice(self.markov_chain[key])
                result.append(next_word)
            else:
                # 如果找不到后续，随机选择新开始
                new_start = random.choice(list(self.markov_chain.keys()))
                result.extend(list(new_start))
        
        return self._post_process(' '.join(result))
    
    def _post_process(self, text):
        """后处理：优化标点和格式"""
        # 修复标点符号间距
        text = re.sub(r'\s*([，。！？；：])', r'\1', text)
        text = re.sub(r'([，。！？；：])\s*', r'\1 ', text)
        # 修复连续标点
        text = re.sub(r'([，。！？；：])\1+', r'\1', text)
        return text
    
    def generate_paragraph(self, num_sentences=5):
        """生成段落"""
        paragraphs = []
        for _ in range(num_sentences):
            sentence = self.generate_text(length=random.randint(20, 50))
            # 确保句子以标点结尾
            if sentence and sentence[-1] not in '。！？':
                sentence += '。'
            paragraphs.append(sentence)
        return ' '.join(paragraphs)
    
    def generate_chapter(self, chapter_num, num_paragraphs=10):
        """生成章节"""
        chapter_title = f"第{chapter_num}章\n"
        content = []
        
        for i in range(num_paragraphs):
            paragraph = self.generate_paragraph(random.randint(3, 8))
            content.append(f"    {paragraph}\n")
            
        return chapter_title + '\n'.join(content)