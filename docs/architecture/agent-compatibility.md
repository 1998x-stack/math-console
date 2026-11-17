# Agent 兼容机制（2026 年 11 月）

| 客户端 | 总规范 | 原生 Agent 文件 | Skill 路径 | 说明 |
| --- | --- | --- | --- | --- |
| OpenCode V2 | AGENTS.md | .opencode/agents/*.md | .agents/skills/ | V2 permissions 数组；主控 primary，专家 subagent |
| Claude Code | CLAUDE.md | .claude/agents/*.md | .claude/skills/ | YAML name、description、tools；可自动匹配或命名委派 |
| Codex | AGENTS.md | .codex/agents/*.toml | .agents/skills/ | 自定义 TOML 角色；需要多 Agent 功能和受信任项目 |
| Pi | AGENTS.md | .pi/agents/*.md | .agents/skills/ | 项目级 Agent 需额外启用 Subagent 扩展与 agentScope |

## 为什么要生成四套而不是复制一份？

Skills 采用统一的 Agent Skills 格式，保留在 .agents/skills/。Claude 通过 .claude/skills/ 的符号链接使用同一套。

但 Agent 不同：Codex 要求 TOML；OpenCode V2 用 permissions 规则；Claude 用特定工具名称的 YAML；Pi 的 example Subagent 扩展使用自己的 Markdown 工具名。四套文件是由 agents/registry.json 自动生成的适配物，并非四个维护源。

## 各平台的实际触发条件

**OpenCode V2：** .opencode/agents 中的 math-conductor 是 primary，其余是 subagent。可以通过 @math-proof-auditor 明确委派；auto-routing 受描述匹配和权限控制，不能保证每次都会自动调用。

**Claude：** .claude/agents 文件在 Agent tool 中可被发现；description 是重要触发信号，但用户明确命名和项目工作规范更可控。只读审校角色只开放 Read/Grep/Glob。

**Codex：** .codex/agents/*.toml 的 name、description、developer_instructions 是必填字段。自定义角色继承父级的权限和 MCP，不支持通过角色文本获得真正的系统级只读隔离。具体多 Agent 调用依宿主会话。

**Pi：** 只放 .pi/agents 不足以触发。请安装 Pi 官方 Subagent 示例扩展，审阅扩展代码并启用 agentScope 为 project 或 both；不要禁用不可信项目的授权提示。不安装扩展时可以使用 .pi/prompts/math-lesson.md 或 Skill 顺序执行，但独立审校仍须外部完成。

## 安全与可用性

模型生成的 Manim Python 只能在隔离环境执行。Agent tool 的工具限权不代替 OS 沙箱。教师签核不可由 Agent 伪造。模型会话重新加载项目配置之前，已启动的会话可能仍持有旧版角色，应重启会话后复验。

文档：
- [Agent Runtime 深度设计](agent-runtime.md)
- [角色注册表](../../agents/registry.json)
- [生成与校验脚本](../../scripts/sync_agents.py)
- [数学内容质量门禁](workbench-pipeline.md)

官方说明：
- https://learn.chatgpt.com/docs/agent-configuration/subagents
- https://opencode.ai/docs/agents
- https://code.claude.com/docs/en/sub-agents
- https://github.com/badlogic/pi-mono/tree/main/packages/coding-agent/examples/extensions/subagent
