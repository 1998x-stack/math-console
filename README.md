# Math Console

面向 AI 数学教育的产品规划、数学知识资产与教学工程方案。

## AI 数学教育三产品规划（2026 年 11 月）

这三个方向共享数学知识、题目、教学分镜、验证机制与学习反馈数据，但面向不同的产品阶段。

| 方向 | 面向用户 | 核心能力 | PDF | 可编辑源文件 |
| --- | --- | --- | --- | --- |
| **A · AI 数学教师工作台** | 教师、教研团队、内容创作者 | 题目解析、数学审校、分镜、Manim 动画与课件 | [PDF · 10 页](docs/product-plans/AI_Math_A_Teacher_Workbench_2026.pdf) | [HTML](docs/product-plans/AI_Math_A_Teacher_Workbench_2026.html) |
| **B · AI 数学交互实验室** | 学生、教师和课堂 | 参数实验、图形探索、预测与验证、课堂活动 | [PDF · 10 页](docs/product-plans/AI_Math_B_Interactive_Lab_2026.pdf) | [HTML](docs/product-plans/AI_Math_B_Interactive_Lab_2026.html) |
| **C · AI 个性化数学导师** | 学生和教师 | 错因识别、分层提示、知识诊断、学习效果评价 | [PDF · 12 页](docs/product-plans/AI_Math_C_Personalized_Tutor_2026.pdf) | [HTML](docs/product-plans/AI_Math_C_Personalized_Tutor_2026.html) |

**建议建设顺序：** A 验证教师真实需求 → B 验证交互式教学效果 → C 在教学效果与隐私安全通过验证后发展个性化辅导。

### 文档涵盖内容

- 产品定位、用户画像、使用场景、核心流程、功能需求与 MVP 范围
- 典型数学教学案例、技术架构、与 Manim / 数学验证引擎的集成思路
- 数据模型、工程交付、质量与可解释性要求
- 90 天行动计划、12 个月路线图、预算情景与商业化边界
- 教学研究、合规风险以及三种产品之间的协同接口

### PDF 构建

三份 HTML 是可版本化的文档源文件。修改对应的 HTML 后，GitHub Actions 会使用 WeasyPrint 与中文字体重新渲染 PDF，并提交到相同目录。

自动构建配置：[`.github/workflows/build-product-plan-pdfs.yml`](.github/workflows/build-product-plan-pdfs.yml)。

本地重新渲染（安装中文字体后）：

```bash
python -m pip install weasyprint==68.0
python - <<'PY'
from pathlib import Path
from weasyprint import HTML

for source in Path("docs/product-plans").glob("AI_Math_*.html"):
    dest = source.with_suffix(".pdf")
    HTML(filename=str(source), base_url=str(source.parent)).write_pdf(str(dest))
    print(dest)
PY
```

> **说明：** 报告为规划草案。预算、定价、用户数量、实施进度和增长目标均为待验证的情景假设，不应直接视为市场事实或产品承诺。

---

## AI 数学教师工作台：Agent & Skills（v0.1）

> 目标：输入数学题目图片，构建 **经过独立审校的解答 Markdown → 教学分镜 → 可编辑 Manim 源码 → 有中文旁白的 MP4 → 课堂练习 PPTX**。本阶段已落地可复用的 Agent 编排与脚本框架；视觉识别、AI 求解、独立证明审校、语音服务及 Docker 执行需要实际连接并完成，不能将模板等同于最终成品。

- **入口**：[AGENTS.md](AGENTS.md)（Codex / OpenCode / Pi）、[CLAUDE.md](CLAUDE.md)（Claude Code）、[Agent.md](Agent.md)（流程索引）。
- **九个 Skills**：[.agents/skills](.agents/skills)（含总流程和八个专业技能）；各自有 `SKILL.md / manifest.json / references / scripts / assets`。
- **四平台原生 Agent**：[角色清单](agents/registry.json)、[运行时深度架构](docs/architecture/agent-runtime.md)。共 10 个 Agent 角色，部署至 `.pi/agents/`、`.opencode/agents/`、`.claude/agents/`、`.codex/agents/`。
- **完整工程规范**：[workbench-pipeline.md](docs/architecture/workbench-pipeline.md)；[跨平台接入](docs/architecture/agent-compatibility.md)。
- **CI 测试**：[validate-agent-skills.yml](.github/workflows/validate-agent-skills.yml)，验证 Skill 元信息、符号链接、Python 语法和示例质量门禁。

### 快速开始

```bash
python -m pip install -r requirements-workbench.txt

# 真实的题目图片（不将学生个人信息提交仓库）
python scripts/math_console.py init --image /path/to/problem.png --run workspaces/lesson-001

# 在 Codex / OpenCode / Pi / Claude 中让 Agent 阅读总流程 Skill，
# 逐阶段编写 problem.json、solution.*、audit.json、storyboard.* ...
python scripts/math_console.py status --run workspaces/lesson-001
python scripts/math_console.py check --stage verify --run workspaces/lesson-001

# 有真实 voiceover.wav 后才可做隔离渲染：
python .agents/skills/math-video/scripts/render_docker.py \
  --run workspaces/lesson-001 --voiceover workspaces/lesson-001/voiceover.wav --build-image

# 练习数据审核完成后生成可编辑 PPTX：
python .agents/skills/math-practice-ppt/scripts/build_slides.py --run workspaces/lesson-001

# 最终交付（必须所有质量门禁通过）：
python scripts/math_console.py release --run workspaces/lesson-001
```

**必须重视：** G2 审校通过前不能生产课堂发布视频；高风险证明需要真人教师签核。Manim Python 来源于模型生成，不得在未隔离的主机执行。仅有结构校验、符号抽样或 ffprobe 检测均不代表教学内容已被数学上证明正确。

## Codex 本地深度迭代

本地 Codex 可直接使用 [主控深度迭代 Prompt](prompts/codex/deep-iteration.md) 进行 Agent/Skill 框架审计、真实题目 E2E、质量门禁测试与分阶段修复；下一轮使用 [继续迭代 Prompt](prompts/codex/continue-iteration.md)。完整启动命令见 [Codex Prompt 使用说明](prompts/codex/README.md)。
