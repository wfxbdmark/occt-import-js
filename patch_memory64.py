#!/usr/bin/env python3
"""
为 occt-import-js 的 CMakeLists.txt 打 memory64 补丁。
放在 fork 仓库根目录，由 GitHub Actions 在 configure 之前执行。

改动：
1. 移除已废弃的 --no-heap-copy（新版 Emscripten 已删除该旗标，否则编译报错）
2. 加入 -sMEMORY64=1（编译 + 链接，开启 64 位寻址）
3. 加入 -sMAXIMUM_MEMORY=8GB（突破 32 位的 2GB 上限）
4. 加入 -sINITIAL_MEMORY=512MB（减少解析过程反复 grow）
"""

import sys
import re

CMAKE = "CMakeLists.txt"

with open(CMAKE, "r", encoding="utf-8") as f:
    src = f.read()

original = src

# 1) 移除 --no-heap-copy
src = src.replace(
    "-sALLOW_MEMORY_GROWTH=1 --no-heap-copy",
    "-sALLOW_MEMORY_GROWTH=1",
)

# 2~4) 在 `--bind` 链接选项之后追加 memory64 相关选项
bind_line = "target_link_options (OcctImportJS PUBLIC --bind)"
memory64_block = bind_line + "\n" + "\n".join([
    "\t# === memory64 patch (突破 wasm32 的 2GB 地址上限) ===",
    "\ttarget_compile_options (OcctImportJS PUBLIC -sMEMORY64=1)",
    "\ttarget_link_options (OcctImportJS PUBLIC -sMEMORY64=1)",
    "\ttarget_link_options (OcctImportJS PUBLIC -sMAXIMUM_MEMORY=8589934592)",
    "\ttarget_link_options (OcctImportJS PUBLIC -sINITIAL_MEMORY=536870912)",
])

if bind_line not in src:
    print("ERROR: 找不到 `--bind` 链接选项行，CMakeLists 结构可能已变。", file=sys.stderr)
    sys.exit(1)

src = src.replace(bind_line, memory64_block, 1)

if src == original:
    print("ERROR: 补丁未产生任何改动。", file=sys.stderr)
    sys.exit(1)

with open(CMAKE, "w", encoding="utf-8") as f:
    f.write(src)

print("memory64 补丁已应用：")
print(" - 移除 --no-heap-copy")
print(" - 新增 -sMEMORY64=1 (compile + link)")
print(" - 新增 -sMAXIMUM_MEMORY=8GB")
print(" - 新增 -sINITIAL_MEMORY=512MB")
