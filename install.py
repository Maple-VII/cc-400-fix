#!/usr/bin/env python3
"""
Claude Auto Fix Hook - 安装脚本

跨平台支持 Windows / macOS / Linux
"""

import json
import shutil
import sys
import platform
from pathlib import Path

# ============================================================
# 常量
# ============================================================

HOOK_FILENAME = "auto_fix_thinking.py"
SCRIPT_DIR = Path(__file__).parent.resolve()

# ============================================================
# 工具函数
# ============================================================

def get_claude_dir() -> Path:
    """获取 Claude 配置目录"""
    return Path.home() / ".claude"


def get_hooks_dir() -> Path:
    """获取 hooks 目录"""
    return get_claude_dir() / "hooks"


def get_settings_path() -> Path:
    """获取 settings.json 路径"""
    return get_claude_dir() / "settings.json"


def get_hook_command() -> str:
    """生成 hook 命令（跨平台，处理空格路径）"""
    hooks_dir = get_hooks_dir()
    hook_path = hooks_dir / HOOK_FILENAME

    if platform.system() == "Windows":
        # Windows: 路径用引号包裹以处理空格
        return f'python "{hook_path}"'
    else:
        # Unix: 使用 python3，使用完整路径（~ 可能不会被展开）
        return f'python3 "{hook_path}"'


def print_status(status: str, message: str):
    """打印状态信息"""
    symbols = {
        "ok": "[OK]",
        "error": "[X]",
        "info": "[*]",
        "warn": "[!]"
    }
    print(f"{symbols.get(status, '[?]')} {message}")


# ============================================================
# 安装逻辑
# ============================================================

def check_prerequisites() -> bool:
    """检查前置条件"""
    claude_dir = get_claude_dir()

    if not claude_dir.exists():
        print_status("error", f"Claude 目录不存在: {claude_dir}")
        print_status("info", "请先安装并运行一次 Claude Code")
        return False

    print_status("ok", f"Claude 目录: {claude_dir}")
    return True


def create_hooks_dir() -> bool:
    """创建 hooks 目录"""
    hooks_dir = get_hooks_dir()

    if hooks_dir.exists():
        print_status("ok", f"hooks 目录已存在: {hooks_dir}")
        return True

    try:
        hooks_dir.mkdir(parents=True, exist_ok=True)
        print_status("ok", f"创建 hooks 目录: {hooks_dir}")
        return True
    except Exception as e:
        print_status("error", f"创建 hooks 目录失败: {e}")
        return False


def copy_hook_script() -> bool:
    """复制 hook 脚本"""
    source = SCRIPT_DIR / HOOK_FILENAME
    dest = get_hooks_dir() / HOOK_FILENAME

    if not source.exists():
        print_status("error", f"源文件不存在: {source}")
        return False

    try:
        shutil.copy2(source, dest)
        print_status("ok", f"复制脚本: {dest}")
        return True
    except Exception as e:
        print_status("error", f"复制脚本失败: {e}")
        return False


def update_settings() -> bool:
    """更新 settings.json，合并 hook 配置"""
    settings_path = get_settings_path()

    # 读取现有配置
    settings = {}
    if settings_path.exists():
        try:
            # 尝试 utf-8-sig 处理 BOM
            with open(settings_path, 'r', encoding='utf-8-sig') as f:
                settings = json.load(f)
            print_status("ok", f"读取现有配置: {settings_path}")
        except Exception as e:
            print_status("warn", f"读取配置失败，将创建新配置: {e}")
            settings = {}

    # 确保 hooks 结构存在
    if "hooks" not in settings:
        settings["hooks"] = {}

    if "UserPromptSubmit" not in settings["hooks"]:
        settings["hooks"]["UserPromptSubmit"] = []

    submit_hooks = settings["hooks"]["UserPromptSubmit"]

    # 检查是否已安装
    already_installed = False
    for hook_entry in submit_hooks:
        # 检查 hooks 中的 command 是否包含我们的脚本
        for h in hook_entry.get("hooks", []):
            if HOOK_FILENAME in h.get("command", ""):
                already_installed = True
                break
        if already_installed:
            break

    if already_installed:
        print_status("info", "Hook 已安装，跳过配置更新")
        return True

    # 添加我们的 hook（使用正确的格式：matcher 必须是字符串）
    hook_command = get_hook_command()
    new_hook_entry = {
        "matcher": "*",  # 匹配所有提示
        "hooks": [
            {
                "type": "command",
                "command": hook_command
            }
        ]
    }
    submit_hooks.append(new_hook_entry)

    # 写回配置
    try:
        with open(settings_path, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)
        print_status("ok", f"更新配置: {settings_path}")
        return True
    except Exception as e:
        print_status("error", f"写入配置失败: {e}")
        return False


def verify_installation() -> bool:
    """验证安装"""
    hook_path = get_hooks_dir() / HOOK_FILENAME
    settings_path = get_settings_path()

    errors = []

    if not hook_path.exists():
        errors.append(f"Hook 脚本不存在: {hook_path}")

    if settings_path.exists():
        try:
            with open(settings_path, 'r', encoding='utf-8-sig') as f:
                settings = json.load(f)

            # 检查 hook 配置
            hooks = settings.get("hooks", {}).get("UserPromptSubmit", [])
            found = False
            for entry in hooks:
                for h in entry.get("hooks", []):
                    if HOOK_FILENAME in h.get("command", ""):
                        found = True
                        break
                if found:
                    break

            if not found:
                errors.append("settings.json 中未找到 hook 配置")

        except Exception as e:
            errors.append(f"验证配置失败: {e}")
    else:
        errors.append(f"settings.json 不存在: {settings_path}")

    if errors:
        for err in errors:
            print_status("error", err)
        return False

    print_status("ok", "安装验证通过")
    return True


def main():
    """主安装流程"""
    print()
    print("=" * 50)
    print("  Claude Auto Fix Hook - 安装程序")
    print("=" * 50)
    print()

    steps = [
        ("检查前置条件", check_prerequisites),
        ("创建 hooks 目录", create_hooks_dir),
        ("复制 hook 脚本", copy_hook_script),
        ("更新 settings.json", update_settings),
        ("验证安装", verify_installation),
    ]

    for step_name, step_func in steps:
        print(f"\n>>> {step_name}")
        if not step_func():
            print()
            print("=" * 50)
            print("  安装失败！请检查上述错误信息")
            print("=" * 50)
            sys.exit(1)

    print()
    print("=" * 50)
    print("  安装成功！")
    print("=" * 50)
    print()
    print("Hook 将在下次发送消息时自动生效。")
    print("如遇 thinking block 签名错误，会自动修复。")
    print()


if __name__ == "__main__":
    main()
