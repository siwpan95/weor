# -*- coding: utf-8 -*-
"""weor 最小测试骨架（离线冒烟：CLI 解析 + 配置 API，不触发 LLM / 不联网）。

运行：
    python -m unittest discover -s tests -v        （仓库根目录）
或：
    python -m unittest tests.test_smoke -v
"""
import os
import sys
import unittest

# 保证任意运行器都能解析 weor 包（仓库根在 sys.path）
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)


class TestCliParser(unittest.TestCase):
    def test_build_parser_and_generate_args(self):
        from weor.cli import build_parser
        parser = build_parser()
        self.assertIsNotNone(parser)
        # 纯解析不执行：generate 子命令带引擎参数
        args = parser.parse_args(["generate", "--engine", "auto"])
        self.assertEqual(args.engine, "auto")

    def test_subcommands_registered(self):
        from weor.cli import build_parser
        parser = build_parser()
        # 子命令可解析（不执行）；config/import 需要各自的位置参数
        parser.parse_args(["generate"])
        parser.parse_args(["library"])
        parser.parse_args(["gui"])
        parser.parse_args(["config", "show"])
        parser.parse_args(["import", "data/sample.txt"])


class TestConfigApi(unittest.TestCase):
    def test_config_class_exists(self):
        from weor.config import Config
        self.assertTrue(callable(Config) or isinstance(Config, type))


if __name__ == "__main__":
    unittest.main()
