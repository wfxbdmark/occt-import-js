#!/usr/bin/env python3
"""
为 occt-import-js 的 CMakeLists.txt 打 memory64 补丁。
放在 fork 仓库根目录，由 GitHub Actions 在 configure 之前执行。

改动：
1. 移除已废弃的 --no-heap-copy（新版 Emscripten 已删除该旗标）
2. 把已废弃的 --bind 换成 -lembind（关键！新版 Emscripten 里 --bind 失效，
   会导致 embind 绑定未被保留 -> 整个 OCCT 被 DCE 清空 -> 空壳 wasm）
3. 加入 -sMEMORY64=1（编译 + 链接，开启 64 位寻址）
4. 加入 -sMAXIMUM_MEMORY=8GB（突破 32 位的 2GB 上限）
5. 加入 -sINITIAL_MEMORY=512MB
"""

import sys

CMAKE = "CMakeLists.txt"

with open(CMAKE, "r", encoding="utf-8") as f:
    src = f.read()

original = src

# 1) 移除 --no-heap-copy
src = src.replace(
    "-sALLOW_MEMORY_GROWTH=1 --no-heap-copy",
    "-sALLOW_MEMORY_GROWTH=1",
)

# 2) --bind -> -lembind（关键修复）
src = src.replace(
    "target_link_options (OcctImportJS PUBLIC --bind)",
    "target_link_options (OcctImportJS PUBLIC -lembind)",
)

# 3~5) 在 -lembind 链接选项之后追加 memory64 相关选项
anchor = "target_link_options (OcctImportJS PUBLIC -lembind)"
memory64_block = anchor + "\n" + "\n".join([
    "\t# === memory64 patch (突破 wasm32 的 2GB 地址上限) ===",
    "\ttarget_compile_options (OcctImportJS PUBLIC -sMEMORY64=1)",
    "\ttarget_link_options (OcctImportJS PUBLIC -sMEMORY64=1)",
    "\ttarget_link_options (OcctImportJS PUBLIC -sMAXIMUM_MEMORY=8589934592)",
    "\ttarget_link_options (OcctImportJS PUBLIC -sINITIAL_MEMORY=536870912)",
])

if anchor not in src:
    print("ERROR: 找不到 -lembind 链接选项行（--bind 替换可能失败）。", file=sys.stderr)
    sys.exit(1)

src = src.replace(anchor, memory64_block, 1)

if src == original:
    print("ERROR: 补丁未产生任何改动。", file=sys.stderr)
    sys.exit(1)

with open(CMAKE, "w", encoding="utf-8") as f:
    f.write(src)

print("memory64 补丁已应用：")
print(" - 移除 --no-heap-copy")
print(" - --bind -> -lembind (关键，避免 embind 绑定被 DCE)")
print(" - 新增 -sMEMORY64=1 (compile + link)")
print(" - 新增 -sMAXIMUM_MEMORY=8GB")
print(" - 新增 -sINITIAL_MEMORY=512MB")
