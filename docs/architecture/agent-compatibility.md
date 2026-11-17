# Agent 运行环境兼容策略

| 引擎 | 入口文件 | Skills | 专业 Agent |
| --- | --- | --- | --- |
| Codex | `AGENTS.md` | `.agents/skills` | 使用内建委派/隔离会话读取角色规范 |
| OpenCode | `AGENTS.md` | `.agents/skills` | `.opencode/agents/*.md` |
| Pi | `AGENTS.md`（供 Agent 主动读取；支持程度以本地版本为准） | `.agents/skills` | 通过会话指令/Skill 组合 |
| Claude Code | `CLAUDE.md` | `.claude/skills` 相对符号链接 | 使用内建子 Agent 或拆分新会话 |

**为何不复制四套 Skills？** 单一源文件避免不同客户端出现不一致的验证规则和危险的默认渲染行为。

**Git 符号链接**：在 Unix/macOS 上 `.claude/skills/<id>` 指向 `../../.agents/skills/<id>`；Windows 需要启用 Developer Mode / `git config core.symlinks true` 后重新检出。如果客户端不跟随链接，用 `python scripts/sync_claude_skills.py --copy` 生成本地副本（忽略跟踪前先删除符号链接；不要提交副本）。**注意：Git 已跟踪的 symlink 用复制替换会导致工作树修改，建议单独工作树。**

**注意**：Skill frontmatter 用标准的 `name`、`description`；详细版本信息归档到 `manifest.json`（平台并不保证自动读取此文件）。脚本在工具可用且授权后执行；认知推理、语音生成和 OCR 需 Agent 或外部服务提供，不是 Skill 自动拥有的能力。

资料：
- https://learn.chatgpt.com/docs/build-skills
- https://opencode.ai/docs/skills
- https://docs.pi.dev/latest/skills
- https://code.claude.com/docs/en/skills
