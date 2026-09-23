# weor — AI 小说生成系统

> 仓库：<https://gitee.com/siwpan/weor> ｜ 许可：MIT（见 [LICENSE](LICENSE)）
> 注：文中 <PATH> 为路径占位符，请替换为你本机实际的目录 / 可执行文件路径。

整合自原 `<PATH>` 散落脚本（autodugeon / fast / fast2 / fast3 / fast4 / media），
并按 2025 年主流开源项目（AI_NovelGenerator / GOAT-Storytelling-Agent / Novel-OS）的范式新增：
**LLM 适配层** + **自上而下生成流水线** + **统一 CLI / GUI / 存储**。

## 特性

- **双引擎**：离线引擎（4 种策略）+ LLM 引擎（OpenAI 兼容 / Ollama），`auto` 模式自动回落
- **统一流水线**：设定 → 角色 → 大纲 → 章节 → 正文，章节间维护全局摘要保证一致性
- **4 种离线策略**：template（来自 autodugeon）/ random（来自 fast）/ markov（来自 fast2）/ nlp（来自 fast4，jieba）
- **统一存储**：单一 `library.db`，整合原 content_library.db + novel_library.db
- **双入口**：CLI + tkinter GUI
- **标签素材导入**：兼容原 `wri.txt` 的 `#characters/#scenes/...` 格式

## 目录结构

```
weor/
├── weor/                      # 整合后包
│   ├── core/
│   │   ├── models.py          # Character/Scene/Chapter/PlotPoint/NovelStructure
│   │   ├── engine_offline.py  # 4 种离线策略
│   │   ├── engine_llm.py      # LLM 引擎（设定→大纲→章节）
│   │   └── pipeline.py        # 编排 + 自动回落
│   ├── adapters/
│   │   ├── llm_adapter.py     # OpenAI 兼容 / Ollama
│   │   └── embedding_adapter.py
│   ├── store/
│   │   ├── library.py         # 统一 SQLite
│   │   └── importer.py        # txt / export.json 导入
│   ├── ui/gui_tk.py           # tkinter GUI
│   ├── config.py              # 配置管理
│   └── cli.py                 # CLI 入口
├── data/                      # wri.txt、export.json
├── output/                    # 生成产物
├── main.py
├── config.example.json
├── requirements.txt
└── README.md
```

## 安装

```bash
pip install -r requirements.txt
# 可选：jieba（用于 nlp 策略）
pip install jieba
```

## 配置

复制 `config.example.json` 为 `config.json`，填入 LLM 配置即可启用 LLM 引擎：

```json
{
  "llm": {
    "api_key": "sk-xxx",
    "base_url": "https://api.deepseek.com/v1",
    "model_name": "deepseek-chat",
    "interface_format": "openai"
  }
}
```

支持的 LLM 端点（任何 OpenAI 兼容接口）：
- DeepSeek、OpenAI、Qwen 通义千问、Kimi、智谱 GLM
- 本地 Ollama（`interface_format: "ollama"`, `base_url: "http://localhost:11434"`）

未配置 `api_key` 时，`auto` 模式自动使用离线引擎。

## 使用

### CLI

```bash
# 离线生成（无需 API key）
python main.py generate --engine offline --genre adventure --chapters 8

# LLM 生成
python main.py generate --engine llm --topic "末世中的最后一封信" --chapters 10

# 自动选择（有 key 用 LLM，否则离线）
python main.py generate --engine auto --genre fantasy --title "龙裔传说"

# 不同离线策略
python main.py generate --engine offline --strategy markov --chapters 5
python main.py generate --engine offline --strategy nlp --chapters 5
```

### GUI

```bash
python main.py gui
```

左侧设置参数，点击「生成小说」，右侧显示结果并自动保存到 `output/`。

### 素材管理

```bash
# 导入标签格式素材
python main.py import data/wri.txt

# 批量导入目录
python main.py import data/

# 导入原 export.json
python main.py import data/export.json

# 查看素材库
python main.py library --list materials
python main.py library --list novels
python main.py library --list stats
```

### 配置检查

```bash
python main.py config init          # 生成 config.example.json
python main.py config show           # 显示当前配置
python main.py config llm-status     # LLM 健康检查
```

## 与原项目的关系

| 原文件 | 整合后位置 |
|--------|-----------|
| `autodugeon.py`（StoryGenerator + 数据结构） | `weor/core/engine_offline.py`（template 策略）+ `weor/core/models.py` |
| `fast.py`（TxtNovelGenerator） | `weor/core/engine_offline.py`（random 策略） |
| `fast2.py`（MarkovNovelGenerator） | `weor/core/engine_offline.py`（markov 策略） |
| `fast3.py`（模板填充） | 合并入 template 策略 |
| `fast4.py`（EnhancedGenerator + jieba） | `weor/core/engine_offline.py`（nlp 策略） |
| `media.py`（tkinter GUI） | `weor/ui/gui_tk.py`（精简重构） |
| `content_import_tool.py`（已丢失） | `weor/store/importer.py`（按 wri.txt 格式重建） |
| `content_library.db` / `novel_library.db` | 统一为 `data/library.db` |

原文件保留在 `<PATH>` 根目录作为参考，未删除。

## 新增能力（相对原项目）

1. **LLM 引擎** — 通过适配器接入大模型，生成质量远超模板/随机/马尔可夫
2. **自上而下流水线** — 设定→角色→大纲→章节，章节间维护全局摘要
3. **统一 CLI** — 所有操作通过子命令统一入口
4. **统一存储** — 解决原项目两个同名 db 的混乱
5. **自动回落** — LLM 失败时无缝切换到离线引擎
6. **配置化** — config.json + 环境变量，便于切换 provider
