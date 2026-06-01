#!/usr/bin/env python3
"""
为 occt-import-js 的 CMakeLists.txt 打 memory64 补丁。
放在 fork 仓库根目录，由 GitHub Actions 在 configure 之前执行。

改动：
0. 【关键】显式定义 EMSCRIPTEN 宏。js-interface.cpp 整个文件被 `#ifdef EMSCRIPTEN`
   包着，而新版 Emscripten 已移除这个旧版预定义宏（只剩 __EMSCRIPTEN__），
   导致 ReadStepFile/EMSCRIPTEN_BINDINGS 被预处理器跳过 -> 空壳 wasm。
0b. C++11 -> C++17。新版 embind 头文件要求 C++17（decay_t / is_pointer_v 等）。
1. 移除已废弃的 --no-heap-copy（新版 Emscripten 已删除该旗标）
2. 把已废弃的 --bind 换成 -lembind（新版 Emscripten 推荐写法）
3. 加入 -sMEMORY64=1（编译 + 链接，开启 64 位寻址）
4. 加入 -sMAXIMUM_MEMORY=8GB（突破 32 位的 2GB 上限）
5. 加入 -sINITIAL_MEMORY=512MB
"""

import sys

CMAKE = "CMakeLists.txt"

with open(CMAKE, "r", encoding="utf-8") as f:
    src = f.read()

original = src

# 0b) C++11 -> C++17（新版 Emscripten 的 embind 头文件要求 C++17：decay_t / is_pointer_v 等）
if "set (CMAKE_CXX_STANDARD 11)" in src:
    src = src.replace("set (CMAKE_CXX_STANDARD 11)", "set (CMAKE_CXX_STANDARD 17)")
elif "set(CMAKE_CXX_STANDARD 11)" in src:
    src = src.replace("set(CMAKE_CXX_STANDARD 11)", "set(CMAKE_CXX_STANDARD 17)")
else:
    print("WARN: 未找到 CMAKE_CXX_STANDARD 11，可能已是其它标准", file=sys.stderr)

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
    "\t# === 关键修复：新版 Emscripten 已移除旧版 EMSCRIPTEN 宏，需显式定义 ===",
    "\t# 否则 js-interface.cpp 的 #ifdef EMSCRIPTEN 为假，ReadStepFile 绑定被跳过",
    "\ttarget_compile_definitions (OcctImportJS PUBLIC EMSCRIPTEN)",
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
print(" - 【关键】定义 EMSCRIPTEN 宏（修复 #ifdef EMSCRIPTEN 导致绑定被跳过）")
print(" - C++11 -> C++17（修复 embind requires -std=c++17 or newer）")
print(" - 移除 --no-heap-copy")
print(" - --bind -> -lembind")
print(" - 新增 -sMEMORY64=1 (compile + link)")
print(" - 新增 -sMAXIMUM_MEMORY=8GB")
print(" - 新增 -sINITIAL_MEMORY=512MB")
