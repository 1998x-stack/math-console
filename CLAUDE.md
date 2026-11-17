# Claude Code — Math Console

优先阅读并执行本仓库 [AGENTS.md](AGENTS.md) 的完整规范；它是四种 Agent 客户端统一使用的单一编排规则。

使用项目中的 `.claude/skills/<id>` 发现技能，其目录为 `.agents/skills/<id>` 的符号链接（不复制第二份技能内容）。脚本、参考、模板都以技能根目录为基准寻址。

接到“图片生成课堂教学包”的任务时，先读取 `math-teacher-pipeline`，按 `intake → solve → verify → storyboard → manim → video → ppt → release` 执行。任何阶段不通过必须停机记录 blocker，不能绕过 G2 独立数学审校。
