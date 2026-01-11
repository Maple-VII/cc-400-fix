#!/usr/bin/env python3
"""
Claude Auto Fix Hook - 卸载脚本

安全移除 hook 配置和脚本文件
"""

import json
import sys
from pathlib import Path

# ============================================================
# 常量
# ============================================================

HOOK_FILENAME = "auto_fix_thinking.py"

# ============================================================
# 工具函数
# ============================================================

def get_claude_dir() -> Path:
    return Path.home() / ".claude"


def get_hooks_dir() -> Path:
    return get_claude_dir() / "hooks"


def get_settings_path() -> Path:
    return get_claude_dir() / "settings.json"


def print_status(status: str, message: str):
    symbols = {
        "ok": "[OK]",
        "error": "[X]",
        "info": "[*]",
        "warn": "[!]"
    }
    print(f"{symbols.get(status, '[?]')} {message}")


# ============================================================
# 卸载逻辑
# ============================================================

def remove_hook_from_settings() -> bool:
    """从 settings.json 移除 hook 配置"""
    settings_path = get_settings_path()

    if not settings_path.exists():
        print_status("info", "settings.json 不存在，跳过")
        return True

    try:
        with open(settings_path, 'r', encoding='utf-8-sig') as f:
            settings = json.load(f)
    except Exception as e:
        print_status("error", f"读取配置失败: {e}")
        return False

    # 获取 UserPromptSubmit hooks
    hooks = settings.get("hooks", {})
    submit_hooks = hooks.get("UserPromptSubmit", [])

    # 过滤掉我们的 hook
    original_count = len(submit_hooks)
    filtered_hooks = []

    for entry in submit_hooks:
        # 检查 command 中是否包含我们的脚本
        keep = True
        for h in entry.get("hooks", []):
            if HOOK_FILENAME in h.get("command", ""):
                keep = False
                break

        if keep:
            filtered_hooks.append(entry)

    removed_count = original_count - len(filtered_hooks)

    if removed_count == 0:
        print_status("info", "settings.json 中未找到 hook 配置")
        return True

    # 更新配置
    settings["hooks"]["UserPromptSubmit"] = filtered_hooks

    # 如果 UserPromptSubmit 为空，可以删除
    if not filtered_hooks:
        del settings["hooks"]["UserPromptSubmit"]

    # 如果 hooks 为空，可以删除
    if not settings["hooks"]:
        del settings["hooks"]

    try:
        with open(settings_path, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)
        print_status("ok", f"已移除 {removed_count} 个 hook 配置")
        return True
    except Exception as e:
        print_status("error", f"写入配置失败: {e}")
        return False


def remove_hook_script() -> bool:
    """删除 hook 脚本文件"""
    hook_path = get_hooks_dir() / HOOK_FILENAME

    if not hook_path.exists():
        print_status("info", "Hook 脚本不存在，跳过")
        return True

    try:
        hook_path.unlink()
        print_status("ok", f"已删除: {hook_path}")
        return True
    except Exception as e:
        print_status("error", f"删除脚本失败: {e}")
        return False


def cleanup_hooks_dir() -> bool:
    """如果 hooks 目录为空，询问是否删除"""
    hooks_dir = get_hooks_dir()

    if not hooks_dir.exists():
        return True

    # 检查是否为空
    remaining = list(hooks_dir.iterdir())
    if remaining:
        print_status("info", f"hooks 目录还有 {len(remaining)} 个文件，保留目录")
        return True

    try:
        hooks_dir.rmdir()
        print_status("ok", f"已删除空目录: {hooks_dir}")
        return True
    except Exception as e:
        print_status("warn", f"删除目录失败: {e}")
        return True  # 非致命错误


def main():
    """主卸载流程"""
    print()
    print("=" * 50)
    print("  Claude Auto Fix Hook - 卸载程序")
    print("=" * 50)
    print()

    steps = [
        ("移除 hook 配置", remove_hook_from_settings),
        ("删除 hook 脚本", remove_hook_script),
        ("清理 hooks 目录", cleanup_hooks_dir),
    ]

    for step_name, step_func in steps:
        print(f"\n>>> {step_name}")
        if not step_func():
            print()
            print("=" * 50)
            print("  卸载过程中遇到错误")
            print("=" * 50)
            sys.exit(1)

    print()
    print("=" * 50)
    print("  卸载完成！")
    print("=" * 50)
    print()


if __name__ == "__main__":
    main()
