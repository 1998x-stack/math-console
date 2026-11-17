# Pi Agent 触发方式

Pi 原生识别根目录 AGENTS.md 及 .agents/skills/，但并**不会自动把 .pi/agents/*.md 当作内置子 Agent 启动**。

已为 10 个职责准备 .pi/agents/*.md，符合 Pi 官方示例 Subagent 扩展的代理格式。要调用这些 Agent，请在你信任的环境中安装并启用该扩展，将 agentScope 配置为 project 或 both，保留不可信项目首次执行的确认提示，然后要求主 Agent 调度 math-conductor、math-proof-auditor 等。

不安装扩展也可通过 /math-lesson （提示模板位于 .pi/prompts/math-lesson.md）或 /skill:math-teacher-pipeline 执行串行任务，但不能将同上下文自我校验说成独立审校。不要默认禁用项目 Agent 信任确认。

文档：https://github.com/badlogic/pi-mono/tree/main/packages/coding-agent/examples/extensions/subagent
