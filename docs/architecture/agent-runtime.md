# Math Console Agent Runtime v0.2

## 1. 主要结论

AI 数学教师工作台不仅需要一段“你是数学教师”的提示词，还需要四层体系：

1. **Project Instructions**：根目录 AGENTS.md / CLAUDE.md 只负责项目边界、安全策略、全局产物规范。
2. **Agent Roles**：由 agents/registry.json 定义每个角色何时触发、哪些文件可读、产物由谁负责、什么时候必须退出。
3. **Skills**：.agents/skills/ 中的 SKILL.md、references/、scripts/ 和 assets/ 负责专业操作方法。
4. **Workflow and Gates**：scripts/math_console.py 和 handoff schema 定义状态流转；没有 Gate pass 不下发需要数学可靠性的后续步骤。

### 既有方案的缺陷

旧版仅有 OpenCode 四个角色、Claude 三个角色，Codex 和 Pi 缺乏相应的原生 Agent 文件。Agent.md 虽可供人阅读，但不是这些工具共同的自动发现机制。让审校 Agent 自称“验证了答案”也无法满足独立性。部分配置还沿用了会随 OpenCode V2 废弃的格式。

新版提供 10 个角色 × 4 套原生文件，且由唯一 Registry 可重复生成；每次 CI 对照文件内容与 Registry，防止某一平台私自放宽审核要求。

## 2. 十个专职角色

| 角色 | 负责阶段 | Skill | 写入权限语义 | 主要交接 |
| --- | --- | --- | --- | --- |
| math-conductor | orchestrate | math-teacher-pipeline | 协调工作区 | 初始化、状态、发布 |
| math-image-interpreter | G0 | math-image-intake | problem.json | 结构化图片题干 |
| math-solver | G1 | math-solution | solution.* | 推导和逐步依据 |
| math-proof-auditor | G2 | math-proof-audit | 只读 | 独立审校报告草案 |
| math-storyboard-designer | G3 | math-storyboard | storyboard.* | 教学画面/旁白 |
| math-pedagogy-reviewer | G3+ | math-storyboard | 只读 | 分镜教研批注 |
| math-manim-engineer | G4a | math-manim | lesson_scene.py | 可编辑 Python |
| math-video-renderer | G4b | math-video | MP4 与日志 | 隔离渲染及真实音轨 |
| math-practice-designer | G4c | math-practice-ppt | practice.* | 分层练习 PPTX |
| math-release-auditor | G5 | math-release-qa | 只读 | 交付审计结论 |

Agent 与 Skill 不要求一一对应：分镜设计与教学审阅共享 Skill，但关注点不同。核心 Agent 可以选择不同基础模型，配置内不硬编码提供商，方便用户在 Codex、Claude、Pi 和 OpenCode 之间切换。

## 3. 输入图片到课堂教学包

主链依次执行：

G0 识图 → G1 规范求解 → G2 独立证明审校 → G3 分镜 → G3+ 教研反馈 → G4a Manim 源码 → G4b 有声 MP4 → G4c 练习 PPT → G5 产物审核。

- **G0**：由具备原生多模态视觉能力的 Agent **直接查看原始图片并理解题干与几何示意图**；不建立 OCR / Python 图片解析脚本。数学上下标、分式、参数范围、几何图标记有歧义时不能进入 G1。脚本仅辅助校验已由 Agent 输出的结构化内容。
- **G1**：必须每小问都有结论，每一步有 reason、step_id、依赖关系。
- **G2**：作者与独立审校者必须是不同 Agent/上下文；脚本会校验 `solution.author.context_id` 与 `audit.reviewer.context_id`（及 agent_id）确实不同，但**这仍然只是结构性约束，不是独立性的证明**。高风险证明必须真实教师批准。脚本只能审查字段，不能证明命题本身。
- **G3**：分镜场景必须追溯已审核的 step_ids；直观动画不可当严格证明。
- **G4a**：交付可以修改的 Manim Community Python；AST 静态检查不是安全沙箱。
- **G4b**：真实执行 Docker/MCP 渲染，生成带实际音轨的 MP4；仅有视频轨、或音轨峰值接近静音，都不能发布（`check_video` 会用 ffmpeg volumedetect 测量峰值）。
- **G4c**：练习题重新审核，PPTX 学生页不得泄露答案，教师页给出分步解析。
- **G5**：发布报告包含真实文件哈希，不能签发未实际生成的 MP4 或教师审批。

## 4. Agent handoff 状态契约

交接记录遵循 agents/handoff.schema.json：

- run_id：唯一执行工作区，避免跨题混合产物。
- stage、agent_id：被指派的责任人和步骤。
- status：pending、blocked、needs-review 或 complete。
- inputs、outputs：实际文件的相对路径，不能填不存在的路径。
- evidence：文件、质量检查、审校、渲染或真人批准的证据路径。
- blockers：精确阻塞原因与返工方向。
- next_agent：通过 Gate 后的下游专职角色。

Handoff 的 JSON Schema 只保证数据形状，不保证证据真实，也不自动给数学命题提供形式化证明。高风险题的 proof obligations 必须保留到独立验证完成为止。

## 5. 委派与并发

主路径必须顺序执行，因为分镜、动画和课件都依赖已经审核的数学推理。独立审校必须在新的上下文中进行，可要求其先独立推导结果再看原答案。

教研 reviewer 可与环境配置检查等**无写冲突**的工作并行。禁止让两个角色同时修改 audit.json 或 storyboard.json，避免丢失审校证据。每个失败 Gate 应保留原始日志并退回对应责任 Agent，而不是重写已提交的审核结论掩盖错误。

上下文隔离不是 OS 沙箱。Pi、Codex、Claude、OpenCode 的子会话都不能代替容器隔离。在任何平台上，生成式 Python 都必须在 Docker 或受控 MCP 中执行。

## 6. 不同客户端的实际限制

**OpenCode V2**：通过 .opencode/agents/*.md 发现；math-conductor 为 primary，其余 subagent。采用 permissions 数组，审校角色禁止编辑与 shell，非审校角色的 shell 需要用户确认。自动路由不等于必然执行。

**Claude Code**：通过 .claude/agents/*.md 的 name、description、tools 发现与委派。专业审校仅赋予 Read/Grep/Glob，避免修改证据。但基础模型仍然可能判断错误，需要人工质检。

**Codex**：通过 .codex/agents/*.toml 定义角色规则文件，项目 .codex/config.toml 的 `[agents]` 配置多 Agent（`enabled`、`max_concurrent_threads_per_session`），**仅在受信任项目加载**。当前会话的 `collaboration.spawn_agent` 已暴露 10 个项目角色的 `agent_type` 枚举。实际以 `agent_type="math-conductor"` 加载角色提示，并由该角色再委派 `math-image-interpreter`；后者报告直接看到了原图且识别出一处待确认歧义。委派任务必须显式给出角色、Skill、输入、输出与文件所有权；不同版本若没有 `agent_type`，应记录能力降级，不能假称角色文件已加载。自定义角色继承父级权限与沙箱，不能凭角色提示假称 OS 级只读。

**Codex 委派自查（可复现）：**

```bash
codex doctor | grep -A6 '^Configuration'   # 确认项目 config.toml 是否被加载
codex exec "列出当前 spawn_agent 的精确参数和 agent_type 枚举；没有则如实说明"
```

**Pi**：.pi/agents/*.md 为兼容官方示例 Subagent 扩展的角色数据。默认 Pi 不自动扫描并运行项目子 Agent，须选择信任该项目并配置扩展 agentScope。未启用扩展时可用 prompt/Skill 主动编排，但不能声称自动实现了独立数学审查。

## 7. 版本迭代、测试与发布

- 单一源：agents/registry.json，登记版本、角色 ID、stage、Skill、触发条件、输入输出与禁止事项。
- 生成器：python scripts/sync_agents.py 为四平台生成原生配置。
- 漂移检测：python scripts/sync_agents.py --check；CI 检查十个角色 × 四个平台一致。
- 角色格式测试：Codex TOML 应可被 tomllib 解析，OpenCode V2 必须使用 permissions，reviewer 应为只读，Pi 文档明确扩展依赖。
- 数据契约：JSON Schema 管理 handoff；升级 Gate 语义或 Agent ID 应视为不兼容变更。

建议语义版本：
- PATCH：措辞与文案、无破坏性错误修复；
- MINOR：增加角色、触发场景、工具适配而兼容已有产物；
- MAJOR：改变 handoff 协议、Gate 契约或者跨平台使用方式。

**尚未完成的生产验证：** 真实 Agent 图像理解与歧义复核、严格证明真人审核、Docker Manim 可重复渲染、中文旁白生成以及对真实课堂练习的教师复核。仓库当前是可执行的 Agent 工程框架，不应宣称已实现端到端全自动可用于教学的产品。

## 8. 建议的维护工作顺序

1. 先更新 agents/registry.json。
2. 运行 python scripts/sync_agents.py。
3. 运行 python scripts/sync_agents.py --check 和单元测试。
4. 通过 GitHub Actions 检查。
5. 从受信任项目目录在每个客户端分别手动触发一个专业 Agent 并检查委派结果。
6. 用真实导数题完成 image → solution → audit → storyboard → manim → voiced mp4 → editable pptx 端到端验收。

官方资料：
- https://learn.chatgpt.com/docs/agent-configuration/subagents
- https://opencode.ai/docs/agents
- https://code.claude.com/docs/en/sub-agents
- https://github.com/badlogic/pi-mono/tree/main/packages/coding-agent/examples/extensions/subagent
