# Math Console — Agent 编排与四平台接入

这是面向维护者的人类可读索引，不是四个平台统一自动加载的 Agent 配置文件。

- 项目总规范：[AGENTS.md](AGENTS.md)
- Claude Code 总规范：[CLAUDE.md](CLAUDE.md)
- 单一角色来源：[agents/registry.json](agents/registry.json)
- 详细架构：[docs/architecture/agent-runtime.md](docs/architecture/agent-runtime.md)
- 统一 Skills：[.agents/skills/](.agents/skills/)

## 原生 Agent 目录

| 客户端 | Agent 文件 | 触发方式 |
| --- | --- | --- |
| OpenCode V2 | [.opencode/agents/](.opencode/agents/) | 主控 primary / 专家 subagent，可 @ 指定或自动匹配 |
| Claude Code | [.claude/agents/](.claude/agents/) | Agent tool 基于 description 调用或用户明确委派 |
| Codex | [.codex/agents/](.codex/agents/) | TOML 角色，通过多 Agent spawn |
| Pi | [.pi/agents/](.pi/agents/) | 必须启用项目级 Subagent 扩展或手动使用 Skills |

## 10 个 Agent 对应 9 个 Skills

主控 math-conductor 负责创建 run、委派和 G0–G5 状态协调。math-image-interpreter、math-solver、math-proof-auditor、math-storyboard-designer、math-pedagogy-reviewer、math-manim-engineer、math-video-renderer、math-practice-designer、math-release-auditor 各自有独立的输入、步骤、交付与停机条件。

两个教研角色使用同一 math-storyboard Skill；Agent 与 Skill 是不同层级，不需要一一映射。

## 维护操作

~~~bash
python scripts/sync_agents.py
python scripts/sync_agents.py --check
python scripts/validate_skill_manifests.py
python -m unittest discover -s tests -p 'test_*.py'
~~~

请只修改 agents/registry.json，然后重新生成四份原生 Agent 配置；不要直接修改自动生成的 Agent 文件。

**安全限制：** 跨 Agent 的不同上下文不等于完整的独立数学证明。高风险证明需要真人教师签核。Codex 子 Agent 沿用父级沙箱和审批；Pi 默认不自动加载项目级自定义 Agent；视频必须经过 Docker/MCP 安全隔离和真实媒体检查。
