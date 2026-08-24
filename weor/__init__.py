"""weor - AI 小说生成系统

整合自原 G:\\weor 散落脚本（autodugeon / fast / fast2 / fast3 / fast4 / media），
并新增 LLM 适配层与自上而下生成流水线。

分层结构：
    core/       — 数据模型 + 离线引擎 + LLM 引擎 + 流水线
    adapters/   — LLM / Embedding 适配器（OpenAI 兼容 / Ollama）
    store/      — SQLite 素材库 + 小说库 + txt 导入器
    ui/         — tkinter GUI
    cli.py      — 命令行入口

快速使用：
    python main.py generate --engine offline --genre adventure --chapters 5
    python main.py generate --engine llm --genre fantasy --chapters 8
    python main.py gui
"""

__version__ = "1.0.0"
__author__ = "weor integrated"
