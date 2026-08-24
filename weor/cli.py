"""命令行入口

子命令：
    generate  生成小说
    gui       启动 tkinter GUI
    import    导入素材（txt 文件/目录/export.json）
    library   查看素材库与小说库
    config    显示/初始化配置

示例：
    python main.py generate --engine auto --genre adventure --chapters 8
    python main.py generate --engine llm --topic "末世中的最后一封信" --chapters 10
    python main.py import data/wri.txt
    python main.py library --list materials
    python main.py gui
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .config import Config, ensure_example_config
from .core.pipeline import Pipeline


def cmd_generate(args, cfg: Config):
    pipe = Pipeline(cfg)
    result = pipe.run(
        title=args.title,
        num_chapters=args.chapters,
        genre=args.genre,
        engine=args.engine,
        strategy=args.strategy,
        topic=args.topic,
        words_per_chapter=args.words,
        save=not args.no_save,
    )
    print("\n" + "=" * 60)
    print(f"标题：《{result.structure.title}》")
    print(f"类型：{result.structure.genre}  引擎：{result.engine_used}")
    print(f"字数：{result.structure.word_count:,}  章节：{len(result.structure.chapters)}")
    if result.output_path:
        print(f"已保存：{result.output_path}")
        print(f"结构 JSON：{result.structure_path}")
    print("=" * 60)
    # 控制台预览前 500 字
    preview = result.text[:500] + ("..." if len(result.text) > 500 else "")
    print("\n--- 预览 ---\n")
    print(preview)


def cmd_gui(args, cfg: Config):
    from .ui.gui_tk import run_gui
    run_gui(cfg)


def cmd_import(args, cfg: Config):
    from .store.library import Library
    from .store.importer import MaterialImporter
    lib = Library(cfg.paths.library_db)
    importer = MaterialImporter(lib)
    target = args.target
    if Path(target).is_dir():
        results = importer.import_directory(target)
        total = sum(v for v in results.values() if v > 0)
        print(f"目录批量导入完成，共 {total} 条素材：")
        for name, cnt in results.items():
            print(f"  {name}: {cnt if cnt >= 0 else '失败'}")
    elif target.endswith(".json"):
        cnt = importer.import_export_json(target)
        print(f"从 {target} 导入 {cnt} 条素材")
    else:
        cnt = importer.import_file(target)
        print(f"从 {target} 导入 {cnt} 条素材")
    # 显示统计
    stats = lib.material_stats()
    if stats:
        print("\n素材库统计：")
        for cat, n in stats.items():
            print(f"  {cat}: {n}")


def cmd_library(args, cfg: Config):
    from .store.library import Library
    lib = Library(cfg.paths.library_db)
    if args.list == "materials":
        items = lib.list_materials(category=args.category, limit=args.limit)
        print(f"素材库（共 {len(items)} 条）：")
        for it in items:
            print(f"  [{it['category']}] {it['content'][:50]}  (used: {it['usage_count']})")
    elif args.list == "novels":
        items = lib.list_novels(limit=args.limit)
        print(f"小说库（共 {len(items)} 条）：")
        for it in items:
            print(f"  #{it['id']} 《{it['title']}》 {it['genre']}/{it['engine']} "
                  f"{it['word_count']}字 {it['chapter_count']}章  {it['created_at'][:16]}")
    elif args.list == "stats":
        stats = lib.material_stats()
        print("素材统计：")
        for cat, n in stats.items():
            print(f"  {cat}: {n}")
    else:
        print("用法：library --list materials|novels|stats [--category X] [--limit N]")


def cmd_config(args, cfg: Config):
    if args.action == "show":
        import json
        print(json.dumps(cfg.to_dict(), ensure_ascii=False, indent=2))
    elif args.action == "init":
        ensure_example_config()
        print(f"已生成 {Path('config.example.json').resolve()}")
        print("复制为 config.json 并填入 api_key 即可启用 LLM 引擎")
    elif args.action == "llm-status":
        if cfg.llm_enabled:
            print(f"LLM 已启用：{cfg.llm.model_name} @ {cfg.llm.base_url}")
            print(f"interface_format: {cfg.llm.interface_format}")
            # 健康检查
            from .adapters.llm_adapter import get_llm_adapter
            adapter = get_llm_adapter(cfg)
            if adapter:
                print("正在健康检查...")
                ok = adapter.health_check()
                print(f"健康检查：{'通过' if ok else '失败'}")
        else:
            print("LLM 未启用（未配置 api_key）")
            print("auto 模式将自动使用离线引擎")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="weor",
        description="weor - AI 小说生成系统（离线引擎 + LLM 引擎）",
    )
    sub = p.add_subparsers(dest="command", required=True)

    # generate
    pg = sub.add_parser("generate", help="生成小说")
    pg.add_argument("--title", default="无名之旅", help="小说标题")
    pg.add_argument("--topic", default="", help="主题/梗概（LLM 引擎用）")
    pg.add_argument("--genre", default=None,
                    choices=["adventure", "fantasy", "mystery", "romance"],
                    help="类型，默认取配置")
    pg.add_argument("--chapters", type=int, default=8, help="章节数")
    pg.add_argument("--words", type=int, default=1500, help="每章字数目标")
    pg.add_argument("--engine", default="auto",
                    choices=["auto", "llm", "offline"], help="引擎选择")
    pg.add_argument("--strategy", default="template",
                    choices=["template", "random", "markov", "nlp"],
                    help="离线策略")
    pg.add_argument("--no-save", action="store_true", help="不保存到 output/")
    pg.set_defaults(func=cmd_generate)

    # gui
    pgui = sub.add_parser("gui", help="启动 tkinter GUI")
    pgui.set_defaults(func=cmd_gui)

    # import
    pi = sub.add_parser("import", help="导入素材")
    pi.add_argument("target", help="txt 文件 / 目录 / export.json")
    pi.set_defaults(func=cmd_import)

    # library
    pl = sub.add_parser("library", help="查看素材库/小说库")
    pl.add_argument("--list", default="stats",
                    choices=["materials", "novels", "stats"])
    pl.add_argument("--category", default=None, help="按素材类别过滤")
    pl.add_argument("--limit", type=int, default=20)
    pl.set_defaults(func=cmd_library)

    # config
    pc = sub.add_parser("config", help="配置管理")
    pc.add_argument("action", choices=["show", "init", "llm-status"])
    pc.set_defaults(func=cmd_config)

    return p


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    cfg = Config.load()
    if hasattr(args, "func"):
        args.func(args, cfg)
        return 0
    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
