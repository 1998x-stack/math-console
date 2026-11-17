# Codex 项目级 Agent

自定义角色使用 .codex/agents/<name>.toml，每份至少包含 name、description、developer_instructions。Codex 的项目 AGENTS.md 仍然是全局工作规则；.codex/config.toml 启用多 Agent（`[agents] enabled` 与 `max_concurrent_threads_per_session`），仅在受信任仓库加载。

**委派能力按当前会话工具契约判定（旧版 CLI 观察可能不同）：**

- 本会话的 `collaboration.spawn_agent` 提供 `agent_type` 参数，枚举中包含 10 个项目数学角色。以 `agent_type: "math-conductor"` 实际调用后，该子 Agent 的开发者提示加载了对应角色规则；它又以 `agent_type: "math-image-interpreter"` 真实委派了视觉角色。
- 委派时应显式传入 `agent_type`，并在任务消息中写明本次输入、输出、文件所有权和所需 Skill。若另一版本工具未暴露该参数，须记录限制，不能把普通子会话冒称已加载专业角色。
- 项目 `.codex/config.toml` **只在受信任仓库生效**。实测：未受信任的 git 仓库中该文件被忽略，`codex doctor` 只报告 `~/.codex/config.toml`。进入仓库时请按要求确认信任，否则 `[agents]` 配置不生效。
- 子 Agent 继承父线程的安全权限、MCP 和沙箱设置；TOML 中不能单独关闭写权限。只读审校是**逻辑角色边界**，不是操作系统权限控制。

复现命令（不写入任何文件）：

```bash
# 1) 先确认项目配置是否被加载
codex doctor | grep -A6 '^Configuration'
# 2) 直接询问模型实际拿到的工具契约
codex exec "列出当前 spawn_agent 工具的精确参数和可用 agent_type；无法看到就如实说明"
```

参考：https://learn.chatgpt.com/docs/agent-configuration/subagents
