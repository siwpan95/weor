# -*- mode: python ; coding: utf-8 -*-
import os

# 入口脚本解析（去本地化）：
#   原硬编码绝对路径已失效，且仓内 legacy/ 下没有 autoplay.py（git ls-files 无命中）。
#   优先级：环境变量 WEOR_SRC（legacy 脚本所在目录）→ SPECPATH 上级目录候选 → fail-loud 并点名变量。
_ENTRY_ENV = 'WEOR_SRC'
_ENTRY = None
_legacy_dir = os.environ.get(_ENTRY_ENV) or os.path.normpath(os.path.join(SPECPATH, '..'))
_cand = os.path.join(_legacy_dir, 'autoplay.py')
if os.path.exists(_cand):
    _ENTRY = _cand
if not _ENTRY:
    raise SystemExit(
        'autoplay.spec: 未找到入口脚本 autoplay.py（仓内不存在此文件，原文件已丢失）。\n'
        '  请设置环境变量 %s 指向存放 autoplay.py 的目录后重试。' % _ENTRY_ENV
    )

a = Analysis(
    [_ENTRY],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='autoplay',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
