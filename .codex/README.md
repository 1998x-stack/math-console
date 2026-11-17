# Codex 项目级 Agent

自定义角色使用 .codex/agents/<name>.toml，每份至少包含 name、description、developer_instructions。Codex 的项目 AGENTS.md 仍然是全局工作规则；.codex/config.toml 启用多 Agent，仅在受信任仓库加载。

在 Codex 中请求：让 math-conductor 处理上传题目，然后 spawn math-proof-auditor 在隔离上下文复核数学证明。Codex 自动选择是否委派取决于模型和会话；不能保证仅存在文件就必然触发。

特别提醒：自定义 Agent 的安全权限、MCP 和沙箱设置**继承父线程**，TOML 中不能单独关闭写权限；只读审校是逻辑角色边界，不是操作系统权限控制。

参考：https://learn.chatgpt.com/docs/agent-configuration/subagents
