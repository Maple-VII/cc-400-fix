# cc-400-fix

自动修复 Claude Code 渠道切换导致的 thinking block 签名错误 (400 Error)。

## 问题场景

当你在不同 API 渠道之间切换时，可能遇到以下错误：

```
API Error 400: Invalid signature in thinking block
API Error 400: thinking.signature: Field required
```

这是因为 thinking block 的签名是加密的，不同渠道之间不兼容。

## 解决方案

本项目提供一个 Claude Code Hook，在每次发送消息前自动检测并修复问题：

- **自动触发**：无需手动操作
- **零数据丢失**：只删除 thinking 块，保留所有对话内容
- **全覆盖**：处理空 signature、无效 signature、reasoning 块

## 安装

### Windows

双击运行 `install.bat`，或在命令行执行：

```cmd
python install.py
```

### macOS / Linux

```bash
chmod +x install.sh
./install.sh
```

或直接运行：

```bash
python3 install.py
```

### 安装验证

安装成功后会显示：

```
==================================================
  安装成功！
==================================================

Hook 将在下次发送消息时自动生效。
如遇 thinking block 签名错误，会自动修复。
```

## 卸载

```bash
python uninstall.py
```

## 工作原理

1. Hook 注册到 Claude Code 的 `UserPromptSubmit` 事件
2. 每次发送消息前，自动扫描会话文件
3. 如检测到问题 thinking 块，自动删除
4. 静默完成，用户无感知

### 处理的块类型

| 类型 | 说明 |
|------|------|
| `thinking` | 标准 thinking 块 |
| `redacted_thinking` | 已编辑的 thinking 块 |
| `reasoning` | 其他 LLM 的推理块 |
| 缺少 `signature` | 格式错误的 thinking 块 |
| 空 `signature` | 签名为空的块 |

## 文件说明

```
cc-400-fix/
├── auto_fix_thinking.py   # 核心 Hook 脚本（安装后复制到 ~/.claude/hooks/）
├── install.py             # 安装脚本
├── install.bat            # Windows 一键安装
├── install.sh             # Unix 一键安装
├── uninstall.py           # 卸载脚本
├── .gitignore             # Git 忽略规则
├── LICENSE                # MIT 许可证
└── README.md              # 本文件
```

## 配置位置

安装后的文件位置：

- Hook 脚本：`~/.claude/hooks/auto_fix_thinking.py`
- 配置文件：`~/.claude/settings.json`

## 手动配置

如需手动配置，在 `~/.claude/settings.json` 中添加：

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/auto_fix_thinking.py"
          }
        ]
      }
    ]
  }
}
```

> Windows 使用 `python` 并转义路径：`python "C:\\Users\\用户名\\.claude\\hooks\\auto_fix_thinking.py"`

## 常见问题

### Q: 安装后没有效果？

1. 确认 `~/.claude/hooks/auto_fix_thinking.py` 文件存在
2. 确认 `~/.claude/settings.json` 中有 hook 配置
3. 重启 Claude Code

### Q: 会丢失对话内容吗？

不会。只删除 thinking 块，所有用户消息和 AI 回复都会保留。

### Q: 影响性能吗？

影响极小。Hook 使用快速预扫描，无问题时不进行任何文件操作。

## 致谢

- 参考了 [cc_400](https://github.com/xuxu777xu/cc_400) 的 Hook 机制设计
- 融合了 [claude-code-cmd-fix-thinking-error](https://github.com/a1exlism/claude-code-cmd-fix-thinking-error) 的完整清理逻辑

## License

MIT
