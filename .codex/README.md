# Codex 项目级 Agent

自定义角色使用 .codex/agents/<name>.toml，每份至少包含 name、description、developer_instructions。Codex 的项目 AGENTS.md 仍然是全局工作规则；.codex/config.toml 启用多 Agent（`[agents] enabled` 与 `max_concurrent_threads_per_session`），仅在受信任仓库加载。

**已实测的 Codex 委派能力（codex-cli 0.157.1，本仓库内实跑）：**

- Codex 确实能委派子 Agent：`spawn_agent(task_name, message, fork_turns, model, reasoning_effort)`；启用 `multi_agent_v2` 后工具名变为 `collaboration.spawn_agent`，参数集合相同。
- 该工具的**参数中没有 role/agent_type**，模型也拿不到任何可选角色枚举值。也就是说，请求“spawn math-proof-auditor”并不能让 Codex 选中 `.codex/agents/` 里的这个角色文件；它只会按你的任务描述开一个新的独立上下文。
- 因此要完成 G2，正确做法不是点名角色，而是**在新上下文里明确要求按 `.agents/skills/math-proof-audit/SKILL.md` 的规则独立重推**，并给出该角色文件路径作为规则来源。
- 项目 `.codex/config.toml` **只在受信任仓库生效**。实测：未受信任的 git 仓库中该文件被忽略，`codex doctor` 只报告 `~/.codex/config.toml`。进入仓库时请按要求确认信任，否则 `[agents]` 配置不生效。
- 子 Agent 继承父线程的安全权限、MCP 和沙箱设置；TOML 中不能单独关闭写权限。只读审校是**逻辑角色边界**，不是操作系统权限控制。

复现命令（不写入任何文件）：

```bash
# 1) 先确认项目配置是否被加载
codex doctor | grep -A6 '^Configuration'
# 2) 直接询问模型实际拿到的工具契约
codex exec -m gpt-6-luna "列出你的 spawn_agent 工具的精确参数名；若没有 role/agent_type 参数就说没有"
```

参考：https://learn.chatgpt.com/docs/agent-configuration/subagents
