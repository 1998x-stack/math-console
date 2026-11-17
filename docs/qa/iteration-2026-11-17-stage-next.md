# 下一阶段工程迭代完成记录（2026-11-17）

## 范围与实测结果

基线：9d19817。当前分支 main 后续提交中已实施下一轮 P0/P1/P2 的工程基础能力。后续运行时的 Agent 原生视觉、真人评价和付费成本数据，不得用静态测试结果冒充。

| 优先级 | 交付 | 状态 | 边界 |
| --- | --- | --- | --- |
| P0 | GitHub Actions 安装 ffmpeg/ffprobe，修复预览测试的环境隔离问题 | 已实现并通过 CI | Ubuntu 上仍有 2 项平台相关单测跳过 |
| P0 | 教师审核改成默认 auto_waiver、严格 strict 可选，并写入 release.json | 已实现，自动测试覆盖 | 策略放行不是教师本人签名，也不能证明运行时审核独立性 |
| P1 | Codex agent_type 委派文档与 Agent/Skills 同步 | 已实现，角色同步测试覆盖 | 不同 Codex 版本仍需在本地验证真实工具契约 |
| P1 | 原创数学视觉基准集（函数导数/解析几何/立体几何） | 已建立 3 个 SVG 题面与 Golden 答案 | 尚未在真实多模态 Agent 上完成评分；不要采用 OCR |
| P1 | Manim MP4 按 beat 抽帧、Agent 逐帧及 PPT 审核、可选 G5 绑定 | 已实现结构与哈希校验 | 真实语义审核由 Agent 自己完成，脚本不会看图、听懂中文或判数学真伪 |
| P2 | Agent 真实事件 usage 汇总与缺失成本防伪 | 已实现统计工具 | 尚未连接本地 Codex 的实际调用事件或账单数据 |

## 核心决策：默认教师免签不是伪造真人批准

- 新工作区默认 teacher_review_policy=auto_waiver；严格模式可在 init 时设置 --teacher-review-policy strict。
- G2 仍需独立数学审校 Agent 与完整推导步骤审查；不能让解题者自己签发审校。
- auto_waiver 只跳过额外的教师签字等待，并在发布报告标为 waived_by_default_policy；不可自动填写 human_review.approved=true。
- strict 要求真实教师声明文件，且 teacher-approval.json 必须与发布文件哈希一致。context_id 不同仍只是结构约束，不能代替来自运行时的独立性证据。

## 可复现命令

```bash
python scripts/sync_agents.py --check
python scripts/validate_skill_manifests.py
python -m unittest discover -s tests -p 'test_*.py' -v
python scripts/math_console.py init --image /path/to/problem.png --run workspaces/demo
# 选择严格真实人工签核时：添加 --teacher-review-policy strict
python scripts/prepare_media_review.py --run workspaces/demo
# 完成真实 Agent 逐场景检查并填写 media-review.json 后：
python scripts/prepare_media_review.py --run workspaces/demo --check
python scripts/summarize_agent_usage.py --events workspaces/demo/reports/agent-events.jsonl
```

## 继续验证的真实事项

1. 基于原图直接给 Codex 等多模态 Agent 启动并记录真实委派事件，扩充视觉基准由 3 道到 30 道并采集评分；不要构建识图 OCR 脚本。
2. 获取可信 Codex runtime 原生 Agent 会话/委派来源。当前 audit.json 中不同 context_id 仍是可以被编写的字符串，不能单独证明独立审校真实发生。
3. 在真实 Docker/MCP 产物上完成视频帧抽查与中文朗读校验，PPT 逐页审阅；把审阅记录归档到被 Git 忽略的 workspaces/。
4. 连接真正的 token/cost/latency usage 源，比较 full 与 slim 两条 Agent 编排路线，而不是推断费用。

本迭代中静态图片 fixture 和报告模板不可当作已经完成真实数学视觉、Manim 教学视频或教师人工审核的证据。
