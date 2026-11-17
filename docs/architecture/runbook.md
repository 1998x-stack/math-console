# AI 教师工作台操作手册

## 1. Agent 客户端调用

**Codex**：在仓库根目录启动，输入“使用 `$math-teacher-pipeline`，对 `/path/to/problem.png` 开始新任务，按 Gate 顺序生成教学包；数学审校委派独立上下文。”

**OpenCode**：在根目录使用 `@math-conductor`，要求调用 `math-teacher-pipeline`；数学证明复核优先由 `math-proof-auditor` 单独执行。

**Pi**：从根目录启动，`/skill:math-teacher-pipeline`，明确图片路径和 `workspaces/<run-id>`；Pi 的可信项目提示需要用户自行确认。

**Claude Code**：读取 `CLAUDE.md`，调用 `/math-teacher-pipeline`（实际技能发现受本地版本、符号链接设置影响）；由 `.claude/agents/math-proof-auditor.md` 子 Agent 独立复核，必要时教师签核。

## 2. 本地命令

```bash
python -m pip install -r requirements-workbench.txt
python scripts/validate_skill_manifests.py
python -m unittest discover -s tests -v

python scripts/math_console.py init --image ~/Desktop/problem.png --run workspaces/example-001
python scripts/math_console.py status --run workspaces/example-001
# 之后由视觉 Agent 按 schema 写 problem.json，G0 通过后继续
python scripts/math_console.py check --stage intake --run workspaces/example-001
```

## 3. 机器可读状态与异常处理

`[PASS]` 仅表明检查脚本当前能观察到的结构/文件条件已满足；`[BLOCKED]` 表明不允许继续交付。Conductor 应将原因反馈到相应 Skill，而不是手动更改 `audit.json` 的 verdict 跳过质量门禁。

## 4. 未来对接接口

准备适配器接口 `VisionTranscribe`、`MathematicalReviewer`、`TTSProvider`、`MCPRenderClient`、`PPTEquationRenderer`，按依赖注入/版本化能力清单实现。当前只提供脚本化 stage gates 和 local Docker 渲染能力，**没有内置自动调用商业模型**。

## 5. 最小验收标准

1. 可解析图片并正确识别符号与每个小问。
2. 复杂证明若无人工签核，`verify` 明确阻塞。
3. 未制作旁白时无声 MP4 不通过 `video`。
4. PPT 保持答案与学生题面隔离且文字可编辑。
5. CI 运行九个 Skill 的 manifest 与符号链接检查、Python 语法与单测。
