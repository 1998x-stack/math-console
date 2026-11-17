# OpenCode V2 Agent 入口

本仓库使用 .opencode/agents/<name>.md，主控 math-conductor 为 mode: primary，其他专家为 mode: subagent。OpenCode 可以自动路由，也可以通过 @math-proof-auditor 等明确调用。各文件采用 V2 的 permissions 数组而不是旧版 permission 键。

验证角色的 edit/shell 显式 deny；非审校角色执行 shell 需要 ask。所有角色都应加载相应 Skill。角色文件来自 agents/registry.json，请勿手工编辑。

参考：https://opencode.ai/docs/agents 和 https://opencode.ai/docs/migrate-v1
