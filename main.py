"""weor 启动器

用法：
    python main.py generate --engine auto --genre adventure --chapters 8
    python main.py generate --engine llm --topic "末世中的最后一封信"
    python main.py gui
    python main.py import data/wri.txt
    python main.py config show
"""
import sys

from weor.cli import main

if __name__ == "__main__":
    sys.exit(main())
