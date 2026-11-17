# Claude Code — Math Console

优先阅读并执行本仓库 [AGENTS.md](AGENTS.md) 的完整规范；它是四种 Agent 客户端统一使用的单一编排规则。

使用项目中的 `.claude/skills/<id>` 发现技能，其目录为 `.agents/skills/<id>` 的符号链接（不复制第二份技能内容）。脚本、参考、模板都以技能根目录为基准寻址。

接到“图片生成课堂教学包”的任务时，先读取 `math-teacher-pipeline`，按 `intake → solve → verify → storyboard → manim → video → ppt → release` 执行。任何阶段不通过必须停机记录 blocker，不能绕过 G2 独立数学审校。

## Claude 原生 Agents

完整专职角色位于 `.claude/agents/*.md`，由 `agents/registry.json` 自动生成并与 Codex / OpenCode / Pi 保持一致。`math-conductor` 负责跨阶段编排，`math-proof-auditor`、`math-pedagogy-reviewer`、`math-release-auditor` 为只读审阅角色。可以在对话中明确要求 Claude 的 Agent tool 委派这些角色；不要把独立证明理解为“同一个模型重复说一遍”。

维护角色请运行 `python scripts/sync_agents.py`，然后 `python scripts/sync_agents.py --check`。
