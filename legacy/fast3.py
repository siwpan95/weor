import random
import re

def create_novel_from_txt():
    """完整的txt素材生成小说流程"""
    
    # 1. 准备素材库（可手动编写或从现有小说提取）
    materials = {
        '开头模板': [
            "那是一个{weather}的{time}，{character}独自一人走在{location}。",
            "传说中，{location}隐藏着{secret}。",
            "{character}从未想过，自己会卷入这场{conflict}。",
            "在一个{weather}的{time}，{character}来到了{location}。",
            "很久以前，{location}流传着一个关于{character}的传说。"
        ],
        '发展模板': [
            "就在这时，{character2}突然出现，{action}。",
            "{character}发现{clue}，这让他{emotion}。",
            "经过一番{action}，{character}终于{result}。",
            "{character2}告诉{character}：{dialogue}",
            "突然，{location}传来一阵{action}的声音。"
        ],
        '高潮模板': [
            "{character}意识到{conflict}已经无法避免。",
            "就在这千钧一发之际，{character}{action}。",
            "{character}的内心充满了{emotion}。"
        ],
        '结尾模板': [
            "最终，{character}{ending}。",
            "故事虽然结束，但{character}的旅程还在继续。",
            "这一切，都只是另一个开始。",
            "{character}站在{location}，望着远方的{weather}，心中充满了{emotion}。"
        ]
    }
    
    # 2. 填充具体内容
    fillers = {
        'character': ['林枫', '月影', '玄真道长', '云飞', '慕容雪', '剑仙'],
        'character2': ['神秘人', '老者', '少女', '少年', '剑客', '故人'],
        'location': ['幽谷', '山庄', '古城', '竹林', '悬崖', '密室', '宫殿'],
        'weather': ['风雨交加', '月明星稀', '大雾弥漫', '阳光明媚', '雪花飘落'],
        'time': ['夜晚', '清晨', '黄昏', '正午', '深夜'],
        'action': ['拔剑相向', '低声细语', '转身离去', '纵身一跃', '抬头望天'],
        'emotion': ['心中一震', '欣喜若狂', '忧心忡忡', '怒火中烧', '感慨万千'],
        'ending': ['找到了真相', '失去了所有', '获得了新生', '选择了离开', '明白了道理'],
        'secret': ['绝世秘籍', '古老宝藏', '惊天秘密', '神秘力量'],
        'conflict': ['风暴', '阴谋', '挑战', '危机', '冒险'],
        'clue': ['一张纸条', '一枚玉佩', '一行古文', '一个线索'],
        'result': ['明白了真相', '找到了答案', '突破了瓶颈', '解开了谜团'],
        'dialogue': ['小心！', '跟我来。', '这是命运的安排。', '一切都会好起来的。']
    }
    
    def fill_template(template, fillers):
        """填充模板"""
        result = template
        for key, value in fillers.items():
            if f'{{{key}}}' in result:
                result = result.replace(f'{{{key}}}', random.choice(value))
        return result
    
    # 3. 生成小说
    novel = []
    novel.append("=" * 50 + "\n")
    novel.append("自动生成小说\n")
    novel.append("=" * 50 + "\n\n")
    
    # 生成开头
    template = random.choice(materials['开头模板'])
    template = fill_template(template, fillers)
    novel.append(template + "\n\n")
    
    # 生成发展段落（5-8段）
    for _ in range(random.randint(5, 8)):
        template = random.choice(materials['发展模板'])
        template = fill_template(template, fillers)
        novel.append("    " + template + "\n\n")
    
    # 生成高潮段落（1-3段）
    for _ in range(random.randint(1, 3)):
        template = random.choice(materials['高潮模板'])
        template = fill_template(template, fillers)
        novel.append("    " + template + "\n\n")
    
    # 生成结尾
    template = random.choice(materials['结尾模板'])
    template = fill_template(template, fillers)
    novel.append("\n" + template + "\n")
    novel.append("\n" + "=" * 50 + "\n")
    novel.append("全书完\n")
    novel.append("=" * 50)
    
    return ''.join(novel)

if __name__ == "__main__":
    # 测试生成
    print(create_novel_from_txt())