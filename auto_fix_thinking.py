#!/usr/bin/env python3
"""
Claude Code Auto Fix Hook - 自动修复 thinking block 签名错误

检测渠道切换，自动清理文件，阻止无效请求。
"""

import json
import sys
import io
import os
import tempfile
from pathlib import Path
from datetime import datetime

# ============================================================
# 常量
# ============================================================

_REMOVED = object()
CLAUDE_HOME = Path.home() / ".claude"
LOG_FILE = CLAUDE_HOME / "auto_fix.log"
CHANNEL_STATE_FILE = CLAUDE_HOME / ".last_channel"
SETTINGS_FILE = CLAUDE_HOME / "settings.json"
DEBUG = os.environ.get("CLAUDE_HOOK_DEBUG", "").lower() in ("1", "true", "yes")


def log(message: str):
    if not DEBUG:
        return
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(f"{datetime.now().isoformat()} | {message}\n")
    except Exception:
        pass


# ============================================================
# 渠道检测
# ============================================================

def get_current_channel() -> str:
    try:
        if SETTINGS_FILE.exists():
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f).get('env', {}).get('ANTHROPIC_BASE_URL', '')
    except Exception:
        pass
    return ''


def get_last_channel() -> str:
    try:
        if CHANNEL_STATE_FILE.exists():
            return CHANNEL_STATE_FILE.read_text(encoding='utf-8').strip()
    except Exception:
        pass
    return ''


def save_channel(url: str):
    try:
        CHANNEL_STATE_FILE.write_text(url, encoding='utf-8')
    except Exception:
        pass


def check_channel_switch() -> tuple:
    """返回 (是否切换, 旧渠道, 新渠道)"""
    current = get_current_channel()
    last = get_last_channel()

    if not current:
        return False, '', ''

    if not last:
        save_channel(current)
        return False, '', current

    if current != last:
        return True, last, current

    return False, last, current

# ============================================================
# 核心逻辑
# ============================================================

def has_problematic_thinking(obj) -> bool:
    """
    快速检测是否存在问题 thinking 块（预扫描优化）

    检测条件：
    1. type 为 'thinking' 或 'redacted_thinking'
    2. type 为 'reasoning'（其他 LLM 的推理块）
    3. type 包含 'thinking' 但缺少 'signature' 字段
    4. signature 为空字符串
    """
    if isinstance(obj, dict):
        block_type = obj.get('type')

        # 标准 thinking 块
        if block_type in ('thinking', 'redacted_thinking'):
            return True

        # reasoning 块（其他 LLM）
        if block_type == 'reasoning':
            return True

        # 空 signature
        if obj.get('signature') == '':
            return True

        # 缺少 signature 的 thinking 块
        if block_type and 'thinking' in str(block_type).lower():
            if 'signature' not in obj:
                return True

        # 递归检查值
        for value in obj.values():
            if has_problematic_thinking(value):
                return True

    elif isinstance(obj, list):
        for item in obj:
            if has_problematic_thinking(item):
                return True

    return False


def remove_thinking_blocks(obj):
    """
    递归删除所有 thinking 块

    返回: (cleaned_obj, removed_count)
    - cleaned_obj: 清理后的对象，如果整个对象需删除则返回 _REMOVED
    - removed_count: 删除的块数量
    """
    removed = 0

    if isinstance(obj, dict):
        block_type = obj.get('type')

        # 删除 thinking/redacted_thinking 块
        if block_type in ('thinking', 'redacted_thinking'):
            return _REMOVED, 1

        # 删除 reasoning 块
        if block_type == 'reasoning':
            return _REMOVED, 1

        # 删除空 signature 的块
        if obj.get('signature') == '':
            return _REMOVED, 1

        # 删除缺少 signature 的 thinking 块
        if block_type and 'thinking' in str(block_type).lower():
            if 'signature' not in obj:
                return _REMOVED, 1

        # 递归处理所有值
        new_dict = {}
        for key, value in obj.items():
            cleaned, count = remove_thinking_blocks(value)
            removed += count
            if cleaned is _REMOVED:
                continue
            new_dict[key] = cleaned

        return new_dict, removed

    elif isinstance(obj, list):
        new_list = []
        for item in obj:
            cleaned, count = remove_thinking_blocks(item)
            removed += count
            if cleaned is _REMOVED:
                continue
            new_list.append(cleaned)

        return new_list, removed

    else:
        return obj, 0


def fix_session_file(filepath: Path, force: bool = False) -> int:
    """
    修复会话文件

    Args:
        filepath: 会话文件路径
        force: 是否强制清理（渠道切换时使用）

    返回: 删除的 thinking 块数量
    """
    log(f"检查文件: {filepath}" + (" [强制模式]" if force else ""))

    if not filepath.exists():
        log(f"文件不存在: {filepath}")
        return 0

    # 强制模式：直接清理，不做预扫描
    # 普通模式：先快速扫描是否有问题
    has_problem = force
    if not force:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        if has_problematic_thinking(data):
                            has_problem = True
                            break
                    except json.JSONDecodeError:
                        continue
        except Exception:
            return 0

    # 无问题则跳过
    if not has_problem:
        log("未发现问题，跳过")
        return 0

    # 有问题，进行修复
    log("发现问题 thinking 块，开始修复...")
    total_removed = 0
    temp_path = None

    try:
        # 使用临时文件确保原子写入
        with open(filepath, 'r', encoding='utf-8') as f_in:
            fd, temp_path = tempfile.mkstemp(
                suffix='.jsonl',
                dir=filepath.parent,
                text=True
            )
            with os.fdopen(fd, 'w', encoding='utf-8') as f_out:
                for line in f_in:
                    line = line.strip()
                    if not line:
                        continue

                    try:
                        data = json.loads(line)
                        cleaned, count = remove_thinking_blocks(data)
                        total_removed += count

                        if cleaned is _REMOVED:
                            continue

                        f_out.write(json.dumps(cleaned, ensure_ascii=False) + '\n')
                    except json.JSONDecodeError:
                        # 保留无法解析的行
                        f_out.write(line + '\n')

        # 替换原文件
        os.replace(temp_path, filepath)
        temp_path = None
        log(f"修复完成，删除了 {total_removed} 个 thinking 块")

    except Exception as e:
        log(f"修复过程出错: {e}")
    finally:
        # 清理临时文件
        if temp_path and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
            except Exception:
                pass

    return total_removed


def main():
    """Hook 入口点"""
    try:
        sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8')
        input_data = json.load(sys.stdin)
        log(f"收到 Hook 输入: session_id={input_data.get('session_id', 'N/A')}")

        transcript_path = input_data.get('transcript_path')
        if not transcript_path:
            log("无 transcript_path，跳过")
            sys.exit(0)

        filepath = Path(transcript_path)

        # 检测渠道切换
        switched, old_ch, new_ch = check_channel_switch()

        if switched:
            log(f"渠道切换: {old_ch} -> {new_ch}")
            # 清理文件
            removed = fix_session_file(filepath, force=True)
            log(f"已清理 {removed} 个 thinking 块")

            if removed > 0:
                # 更新渠道记录
                save_channel(new_ch)
                # 阻止请求，通过 stderr 提示用户
                msg = f"""
╔══════════════════════════════════════════════════════════╗
║  ⚡ Auto Fix - 渠道切换检测                              ║
╠══════════════════════════════════════════════════════════╣
║  已清理 {removed} 个 thinking 块，会话文件已修复。
║  请重启 Claude Code 以加载修复后的会话。                 ║
╚══════════════════════════════════════════════════════════╝
"""
                sys.stderr.buffer.write(msg.encode('utf-8'))
                sys.exit(2)  # Exit code 2 = 阻止请求
            else:
                # 没有需要清理的，更新记录并继续
                save_channel(new_ch)
        else:
            # 普通模式：检测并清理
            removed = fix_session_file(filepath, force=False)
            log(f"处理完成，共删除 {removed} 个块")

    except Exception as e:
        log(f"Hook 异常: {e}")

    sys.exit(0)


if __name__ == '__main__':
    main()
