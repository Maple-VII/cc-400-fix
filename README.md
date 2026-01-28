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

本项目提供一个 Claude Code Hook，自动检测渠道切换并修复问题：

- **智能检测**：仅在渠道切换时触发清理
- **自动阻止**：清理后阻止无效请求，提示重启
- **零数据丢失**：只删除 thinking 块，保留所有对话内容
- **全覆盖**：处理 thinking、redacted_thinking、reasoning 块

## 工作流程

```
切换渠道 → 发送消息 → Hook 检测到切换
    ↓
清理会话文件中的 thinking 块
    ↓
阻止本次请求，提示重启
    ↓
重启 Claude Code → 正常使用
```

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

### Windows

双击运行 `uninstall.bat`，或：

```cmd
python uninstall.py
```

### macOS / Linux

```bash
python3 uninstall.py
```

## 工作原理

1. Hook 注册到 Claude Code 的 `UserPromptSubmit` 事件
2. 每次发送消息前，检测当前渠道是否与上次不同
3. 如检测到渠道切换，强制清理会话文件中的 thinking 块
4. 清理后阻止请求（exit code 2），提示用户重启
5. 重启后 Claude Code 加载干净的会话文件，正常使用

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
├── uninstall.bat          # Windows 一键卸载
├── .gitignore             # Git 忽略规则
├── LICENSE                # MIT 许可证
└── README.md              # 本文件
```

## 配置位置

安装后的文件位置：

- Hook 脚本：`~/.claude/hooks/auto_fix_thinking.py`
- 配置文件：`~/.claude/settings.json`
- 渠道状态：`~/.claude/.last_channel`（自动生成）

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

## 调试模式

如需查看 Hook 运行日志，在 `~/.claude/settings.json` 的 `env` 中添加：

```json
{
  "env": {
    "CLAUDE_HOOK_DEBUG": "1"
  }
}
```

日志文件位置：`~/.claude/auto_fix.log`

## 常见问题

### Q: 安装后没有效果？

1. 确认 `~/.claude/hooks/auto_fix_thinking.py` 文件存在
2. 确认 `~/.claude/settings.json` 中有 hook 配置
3. 重启 Claude Code

### Q: 会丢失对话内容吗？

不会。只删除 thinking 块，所有用户消息和 AI 回复都会保留。

### Q: 每次切换渠道都需要重启吗？

是的。由于 Claude Code 在启动时加载会话到内存，Hook 清理文件后需要重启才能加载修复后的内容。但这只发生在渠道切换且有 thinking 块需要清理时。

### Q: 影响性能吗？

影响极小。Hook 使用快速预扫描，无问题时不进行任何文件操作。

## 致谢

- 参考了 [cc_400](https://github.com/xuxu777xu/cc_400) 的 Hook 机制设计
- 融合了 [claude-code-cmd-fix-thinking-error](https://github.com/a1exlism/claude-code-cmd-fix-thinking-error) 的完整清理逻辑

## License

MIT
