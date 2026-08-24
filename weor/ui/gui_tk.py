"""tkinter GUI

精简整合自原 media.py（2347 行 tkinter 可视化），保留其「Canvas 动效 + 状态面板」思路，
但聚焦于小说生成场景：左侧参数面板 + 右侧生成结果展示 + 底部进度动画。

避免阻塞主线程：生成任务在子线程中运行，通过 queue 回传进度与结果。
"""
from __future__ import annotations

import os
import queue
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from typing import Optional

from ..config import Config
from ..core.pipeline import Pipeline


GENRES = [("冒险", "adventure"), ("奇幻", "fantasy"),
          ("悬疑", "mystery"), ("爱情", "romance")]
ENGINES = [("自动", "auto"), ("LLM", "llm"), ("离线", "offline")]
STRATEGIES = [("模板", "template"), ("随机", "random"),
              ("马尔可夫", "markov"), ("NLP", "nlp")]


class PerformanceMonitor:
    """简单帧计数器（保留 media.py 的性能监控思路）"""
    def __init__(self):
        self.frames = 0
        self.start = 0.0

    def tick(self):
        self.frames += 1


class NovelGeneratorGUI:
    """小说生成 GUI 主窗口"""

    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.root = tk.Tk()
        self.root.title("weor - AI 小说生成系统")
        self.root.geometry("980x680")
        self.root.minsize(800, 560)
        self._task_queue: queue.Queue = queue.Queue()
        self._gen_thread: Optional[threading.Thread] = None
        self.monitor = PerformanceMonitor()
        self._build_ui()
        self._poll_queue()

    # ---------- UI 构建 ----------
    def _build_ui(self):
        # 顶部标题
        top = ttk.Frame(self.root, padding=8)
        top.pack(fill="x")
        ttk.Label(top, text="weor 小说生成", font=("Microsoft YaHei", 16, "bold")
                  ).pack(side="left")
        self.status_label = ttk.Label(top, text="就绪", foreground="#555")
        self.status_label.pack(side="right")

        # 主体：左参数 + 右结果
        body = ttk.PanedWindow(self.root, orient="horizontal")
        body.pack(fill="both", expand=True, padx=8, pady=4)

        # 左侧参数面板
        left = ttk.Frame(body, padding=10, width=300)
        body.add(left, weight=0)
        self._build_params(left)

        # 右侧结果
        right = ttk.Frame(body, padding=10)
        body.add(right, weight=1)
        self._build_result(right)

        # 底部进度
        bottom = ttk.Frame(self.root, padding=8)
        bottom.pack(fill="x")
        self.progress = ttk.Progressbar(bottom, mode="indeterminate", length=400)
        self.progress.pack(side="left", padx=4)
        self.engine_info = ttk.Label(bottom, text="", foreground="#888")
        self.engine_info.pack(side="left", padx=12)

    def _build_params(self, parent):
        # 标题
        ttk.Label(parent, text="小说标题：").pack(anchor="w", pady=(4, 0))
        self.title_var = tk.StringVar(value="无名之旅")
        ttk.Entry(parent, textvariable=self.title_var).pack(fill="x")

        # 主题
        ttk.Label(parent, text="主题/梗概（LLM 用）：").pack(anchor="w", pady=(8, 0))
        self.topic_var = tk.StringVar(value="一场改变命运的冒险")
        ttk.Entry(parent, textvariable=self.topic_var).pack(fill="x")

        # 类型
        ttk.Label(parent, text="类型：").pack(anchor="w", pady=(8, 0))
        self.genre_var = tk.StringVar(value="adventure")
        for label, val in GENRES:
            ttk.Radiobutton(parent, text=label, value=val,
                            variable=self.genre_var).pack(anchor="w")

        # 引擎
        ttk.Label(parent, text="引擎：").pack(anchor="w", pady=(8, 0))
        self.engine_var = tk.StringVar(value="auto")
        for label, val in ENGINES:
            ttk.Radiobutton(parent, text=label, value=val,
                            variable=self.engine_var).pack(anchor="w")

        # 离线策略
        ttk.Label(parent, text="离线策略：").pack(anchor="w", pady=(8, 0))
        self.strategy_var = tk.StringVar(value="template")
        for label, val in STRATEGIES:
            ttk.Radiobutton(parent, text=label, value=val,
                            variable=self.strategy_var).pack(anchor="w")

        # 章节数
        ttk.Label(parent, text="章节数：").pack(anchor="w", pady=(8, 0))
        self.chapters_var = tk.IntVar(value=8)
        ttk.Spinbox(parent, from_=1, to=50, textvariable=self.chapters_var
                    ).pack(fill="x")

        # LLM 状态提示
        self.llm_hint = ttk.Label(
            parent, text=self._llm_hint_text(), foreground="#888", wraplength=240)
        self.llm_hint.pack(anchor="w", pady=(10, 0))

        # 生成按钮
        ttk.Button(parent, text="生成小说", command=self._on_generate
                   ).pack(fill="x", pady=(12, 0))
        ttk.Button(parent, text="保存到文件", command=self._on_save
                   ).pack(fill="x", pady=(4, 0))

    def _build_result(self, parent):
        ttk.Label(parent, text="生成结果：").pack(anchor="w")
        self.result_text = scrolledtext.ScrolledText(
            parent, wrap="word", font=("Microsoft YaHei", 11), bg="#fafafa")
        self.result_text.pack(fill="both", expand=True, pady=4)

        meta = ttk.Frame(parent)
        meta.pack(fill="x")
        self.meta_label = ttk.Label(meta, text="字数：0 | 章节：0 | 引擎：—", foreground="#555")
        self.meta_label.pack(side="left")

    def _llm_hint_text(self) -> str:
        if self.cfg.llm_enabled:
            return f"LLM 已启用：{self.cfg.llm.model_name} @ {self.cfg.llm.base_url}"
        return "LLM 未启用（未配置 api_key），auto 模式将使用离线引擎"

    # ---------- 生成 ----------
    def _on_generate(self):
        if self._gen_thread and self._gen_thread.is_alive():
            messagebox.showinfo("提示", "正在生成中，请稍候")
            return
        self.result_text.delete("1.0", "end")
        self.result_text.insert("end", "生成中...\n")
        self.status_label.config(text="生成中…")
        self.progress.start(10)
        self._gen_thread = threading.Thread(
            target=self._generate_worker, daemon=True)
        self._gen_thread.start()

    def _generate_worker(self):
        try:
            pipe = Pipeline(self.cfg)
            result = pipe.run(
                title=self.title_var.get() or "无名之旅",
                num_chapters=self.chapters_var.get(),
                genre=self.genre_var.get(),
                engine=self.engine_var.get(),
                strategy=self.strategy_var.get(),
                topic=self.topic_var.get(),
                save=True,
            )
            self._task_queue.put(("ok", result))
        except Exception as e:
            self._task_queue.put(("err", str(e)))

    def _poll_queue(self):
        try:
            kind, payload = self._task_queue.get_nowait()
            if kind == "ok":
                result = payload
                self.result_text.delete("1.0", "end")
                self.result_text.insert("end", result.text)
                self.meta_label.config(
                    text=f"字数：{result.structure.word_count:,} | "
                         f"章节：{len(result.structure.chapters)} | "
                         f"引擎：{result.engine_used}")
                self.status_label.config(text="生成完成")
                if result.output_path:
                    messagebox.showinfo(
                        "完成",
                        f"小说已生成并保存：\n{result.output_path}")
            else:
                self.result_text.delete("1.0", "end")
                self.result_text.insert("end", f"生成失败：\n{payload}")
                self.status_label.config(text="失败")
        except queue.Empty:
            pass
        self.root.after(200, self._poll_queue)

    def _on_save(self):
        content = self.result_text.get("1.0", "end").strip()
        if not content:
            messagebox.showwarning("提示", "还没有内容可保存")
            return
        from tkinter import filedialog
        path = filedialog.asksaveasfilename(
            defaultextension=".txt", filetypes=[("文本", "*.txt")],
            initialfile=self.title_var.get() or "novel")
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            messagebox.showinfo("已保存", path)

    # ---------- 运行 ----------
    def run(self):
        self.root.mainloop()


def run_gui(cfg: Optional[Config] = None) -> None:
    """启动 GUI"""
    cfg = cfg or Config.load()
    NovelGeneratorGUI(cfg).run()
