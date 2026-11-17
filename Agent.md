# Agent · AI 数学教师工作台

这是人类阅读的 Agent 索引。**实际自动发现的项目指令是 [AGENTS.md](AGENTS.md)**；Claude Code 使用 [CLAUDE.md](CLAUDE.md)。

主控 Agent 按八个阶段编排：题目识别 → 数学求解 → 独立审校 → 教学分镜 → Manim 编程 → 视频制作 → 练习 PPT → 发布质检。

- 总流程 Skill：[`math-teacher-pipeline`](.agents/skills/math-teacher-pipeline/SKILL.md)
- 详细状态机、责任矩阵和失败回滚：[工作台流程](docs/architecture/workbench-pipeline.md)
- 多平台配置：[Agent 兼容说明](docs/architecture/agent-compatibility.md)
- 命令行：`python scripts/math_console.py --help`
- 所有 Skills 的版本与交付定义：`.agents/skills/*/manifest.json`

重要：G2 数学审校 **不能由作者自身宣布通过**；复杂证明需要人工复核。没有真实音轨/渲染或未完成质量门禁时，不得宣称最终交付。
