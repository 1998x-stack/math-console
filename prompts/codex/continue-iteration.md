# Math Console · Codex 后续迭代 Prompt

请先读取本仓库 prompts/codex/deep-iteration.md 和上一轮实际执行报告。现在继续进行下一轮**基于测试证据的增量迭代**，不要从头重写项目或只输出建议。

1. 检查当前 git status，保护已有工作区与用户改动；读取 workspaces/<RUN_ID>/reports/ 下真正存在的报告、失败日志和质量门禁状态。
2. 按 P0 > P1 > P2 优先处理最重要、可复现的三个问题。每个问题必须先给失败测试，再做最小修复，随后运行回归测试并记录退出码。
3. Agent 角色变更只能修改 agents/registry.json 后运行 python scripts/sync_agents.py；Skill 变更必须同步 SKILL.md、references/、manifest.json 与关联测试，避免四平台漂移。
4. 数学审校必须由不同上下文的 math-proof-auditor 执行，高风险需要真人教师审核。没有实际审校/音轨/视频/图片时只标为 BLOCKED 或 UNVERIFIED，不得修饰为 PASS。
5. 运行 python scripts/sync_agents.py --check、python scripts/validate_skill_manifests.py、python -m unittest discover -s tests -p test_*.py -v，以及所修阶段的 math_console check。
6. 若有真实图片、TTS 音轨、Docker，则继续端到端；否则完成可独立验证的工程部分并明确列出阻塞原因。
7. 不自动 git commit / push / PR，不执行未知 Manim Python 于宿主，不覆盖用户数据。结束时输出：修复文件、测试前后证据、实际 Agent 委派记录、G0-G5 状态、产物路径、下轮三项优先级。

现在立即读取上一轮实际日志与 git status，从最高优先级问题开始动手。
