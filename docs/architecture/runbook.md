# AI 教师工作台操作手册

## 1. Agent 客户端调用

**Codex**：在仓库根目录启动（并确认信任该项目，否则 `.codex/config.toml` 不生效），输入“使用 `math-teacher-pipeline`，对 `/path/to/problem.png` 开始新任务，按 Gate 顺序生成教学包；**另开一个独立上下文**，要求按 `.agents/skills/math-proof-audit/SKILL.md` 独立重推”。注意：Codex 的 `spawn_agent` 没有 role/agent_type 参数，无法点名 `math-proof-auditor`，只能靠任务描述与 Skill 路径约束角色行为；详见 `.codex/README.md`。

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

# 全部内容门禁 + 草稿门禁（practice 不需要视频即可验证）
python scripts/math_console.py check --stage all --run workspaces/example-001
# 只有练习与 PPT 提前就绪时（不要求已有视频）
python scripts/math_console.py check --stage practice --run workspaces/example-001
# 发布后复核：任何产物被改动都会判定 release.json 过期
python scripts/math_console.py check --stage release --run workspaces/example-001
python scripts/math_console.py release --run workspaces/example-001

# 没有真实旁白时只能生成无声预览，不会创建 lesson.mp4
python .agents/skills/math-video/scripts/render_docker.py --run workspaces/example-001 --preview-only
```

> **Python 版本：** 必须使用 **Python 3.11+**（CI 与本地验收使用 3.12）。`scripts/sync_agents.py` 和 Codex TOML 测试依赖标准库 `tomllib`；若用 3.9/3.10，脚本会以退出码 2 明确提示版本要求，而不是抛出裸 `ImportError`。macOS 上系统自带的 `/usr/bin/python3` 通常是 3.9，请用 `python3.12` 运行，例如 `python3.12 -m unittest discover -s tests -v`。

> **Gate 契约版本（v0.3）：** 在 v0.2 基础上，门禁新增：
> - **G4c 分区取证**：`practice.pptx` 每页必须以 `学生练习` / `教师答案` 开头声明分区；题面只能出现在学生页，`答案：…` 只能出现在教师答案页，且基础/迁移/挑战三层必须齐备。
> - **G4b 一致性**：分镜声明总时长与成片时长偏差需 ≤ `max(10s, 35%)`；音轨时长与画面偏差过大（> `max(3s, 10%)`）判为音画不同步。
> - **G4b 预览模式**：`render_docker.py --preview-only` 在隔离容器中产出 `silent.mp4`，**不生成** `lesson.mp4`。
> - **G5 可复核**：`release.json` 记录 `toolchain` 与 `gate_evidence`；`check --stage release` 重新比对全部哈希，上游文件改动即判定过期（`--stage all` 在 release.json 存在时也会复核）。

> **Gate 契约版本（v0.2）：** `solution.schema.json` 与 `audit.schema.json` 已升级到 `schema_version: 0.2.0`。新增要求：解答必须声明 `author`（`agent_id`/`context_id`/`route`），审校必须声明 `reviewer.context_id`，且 G2 会拒绝**同上下文或同 Agent 自我审校**；`risk_level=standard` 需要 `risk_rationale`，任一步骤标记 `proof_obligation` 则强制高风险并要求教师签核。旧的 0.1.0 产物会被明确拒绝，需要补齐字段。

## 3. 机器可读状态与异常处理

`[PASS]` 仅表明检查脚本当前能观察到的结构/文件条件已满足；`[BLOCKED]` 表明不允许继续交付。Conductor 应将原因反馈到相应 Skill，而不是手动更改 `audit.json` 的 verdict 跳过质量门禁。

## 4. 未来对接接口

准备适配器接口 `VisionTranscribe`、`MathematicalReviewer`、`TTSProvider`、`MCPRenderClient`、`PPTEquationRenderer`，按依赖注入/版本化能力清单实现。当前只提供脚本化 stage gates 和 local Docker 渲染能力，**没有内置自动调用商业模型**。

## 5. 最小验收标准

1. 可解析图片并正确识别符号与每个小问。
2. 复杂证明若无人工签核，`verify` 明确阻塞。
3. 未制作旁白时无声 MP4 不通过 `video`（`check_video` 用 ffmpeg volumedetect 测量音轨峰值，接近静音即阻塞）；分镜声明时长与成片时长必须一致。
4. PPT 保持答案与学生题面隔离且文字可编辑（按页首分区取证，三层题型齐备）。
5. CI 运行九个 Skill 的 manifest 与符号链接检查、Python 语法与单测。


## 6. 四平台原生 Agent（v0.2）

- OpenCode：`.opencode/agents/math-conductor.md` 是 primary；其余 9 个角色可通过 `@math-proof-auditor` 等显式委派。使用 V2 `permissions` 格式。
- Claude Code：`.claude/agents/*.md` 由 Agent tool 发现，支持手动命名和描述匹配。
- Codex：`.codex/agents/*.toml` 是角色规则文件，`.codex/config.toml` 的 `[agents]` 启用多 Agent（仅在受信任项目加载）。**实测 0.157.1 的 `spawn_agent` 没有 role/agent_type 参数**，所以不能“按名称 spawn 对应角色”；只能把角色 Skill 路径与任务描述一起交给新上下文。子 Agent 继承父级权限，不存在独立只读沙箱保证。
- Pi：`.pi/agents/*.md` 必须配合项目可信 Subagent 扩展与 agentScope=project/both；没有扩展时使用 `/math-lesson` 提示模板或 Skills 串行调用。

上述原生文件由 `agents/registry.json` 唯一生成：

~~~bash
python scripts/sync_agents.py --check
python -m unittest discover -s tests -p 'test_agent_profiles.py' -v
~~~

角色责任、Gate 转移和失败回滚见 `docs/architecture/agent-runtime.md`。
