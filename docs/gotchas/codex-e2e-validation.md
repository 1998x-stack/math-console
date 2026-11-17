# Codex 本地端到端验证踩坑记录

本页记录 2026-11-17 的一轮真实函数与导数题测试。原图、解答、音视频、PPTX 和教师声明均留在被 Git 忽略的 `workspaces/<run-id>/`；不要把学生图片或教学包提交到公开仓库。

## 1. 先看图，再调用脚本

`math_console.py init` 只复制原图并计算 SHA-256，不理解题面。主 Agent 或真正能看到附件的视觉 Agent 必须先直接复述题干、公式、图形与全部小问。此次第（3）问的 `m.n`/`m,n` 模糊处必须由用户确认；不能靠 OCR、路径或脚本的结构 PASS 消除语义歧义。

## 2. Codex 角色能力按当前工具契约判断

旧文档曾声称 `spawn_agent` 没有 `agent_type`。本轮真实工具提供该参数，`math-conductor` 曾按角色加载并委派 `math-image-interpreter`；其余专业角色也分别按角色调用。不同 Codex 版本的工具契约可能变化，启动时先检查可用参数和角色枚举，不能仅凭 `.codex/agents/*.toml` 文件存在宣称专业 Agent 已运行。`python scripts/sync_agents.py --check` 只证明生成配置与 registry 一致，不证明执行过委派。

## 3. 使用项目 Python 虚拟环境

本机 `python3` 是 3.9，`python3.12` 虽可执行但缺 Pillow；`.venv/bin/python` 为 3.12 且有工作台依赖。复现时使用：

```bash
.venv/bin/python scripts/math_console.py status --run workspaces/<run-id>
.venv/bin/python -m unittest discover -s tests -p 'test_*.py'
```

Python 检查工具只验证文件、结构和可计算的媒体属性，不证明数学正确性。

## 4. 独立审校与教师声明分开留痕

独立 `math-proof-auditor` 要从题目重推，不能由 `math-solver` 自签。高风险全称命题需要真实教师批准；Agent 审校 PASS 与教师批准是两项不同证据。一次明确的教师声明可覆盖**已存在、已展示且范围清楚的当前教学包**；记录声明原文、声明时间、适用 run 和产物版本。本轮把声明存为 `teacher-approval.json`，其 SHA-256 清单须与全部发布产物一致，发布报告也为证据文件记哈希。不要将“默认通过”当作未来题目已经被真人审阅，也不要把旧签核延伸到后来才生成的新练习。

## 5. Manim 必须隔离渲染并逐帧抽查

本轮 `lesson_scene.py` 静态 lint PASS，但 Docker 首轮成片仍在二次函数推导场景出现 underbrace 与下一行重叠，另一个参数场景的标签也靠近标题。源码修正间距后重新隔离渲染，抽查开场、参数分类、极值、证明与结尾关键帧才通过。静态 lint、MP4 有视频流和音频流都不能替代画面检查。

Docker 镜像依赖较大的 Manim 基础层和 Noto CJK 字体；首次拉取可能耗时。安全渲染仍使用项目的 `render_docker.py`，保留断网、只读源码挂载、资源限额。不要在宿主直接运行模型生成的 Manim Python。

## 6. 中文 TTS 要按分镜对齐

本机 `say -v Tingting` 可生成实际中文旁白。按 beat 合成并在语句尾补合理停顿，不截断证明；本轮 212 秒音轨与 212.73 秒成片匹配。用 `ffprobe` 确认 H.264/AAC，用 `ffmpeg` 解码并测峰值；仅有音频流不等于有真实旁白。数学符号应在分镜中先写清中文读法，例如“G 下标 m，括号 x”。

## 7. PPTX 字体声明与渲染环境是两件事

硬编码 `Microsoft YaHei` 会在没有该字体的 macOS 上触发不可预期回退。课件构建器现在按平台设定中文字体，并在 OOXML run 写东亚字体属性 `a:ea`。每道练习的 `teaching_objective` 已纳入 `practice.schema.json` 0.2.0；变更契约时要同步 Skill、示例、manifest 和测试。

本机 LibreOffice 26.8 无界面导出最初把中文画成空白或方框，尽管 PPTX 的 OOXML 含完整中文。根因是默认 fontconfig 没有读取用户字体目录。验收时使用独立的 `FONTCONFIG_FILE`，包含用户字体目录和缓存目录，并为 LibreOffice 采用全新 profile；确认 `pdffonts` 实际嵌入 CJK 字体后，再将 PDF 每页渲成 PNG 逐页查看。只看 `pdftotext` 或 PPT 首页不能证明所有页面可读。

## 8. 发布与提交边界

`release.json` 只能在各门禁真实通过后由程序生成并再次执行 `check --stage release`。本地 `workspaces/`、`output/`、根目录 `/media/` 与常见缓存/构建输出由 `.gitignore` 排除；提交应只包含 Agent/Skill/脚本/测试/文档修改。推送前运行全套单测、角色同步检查、Skill manifest 检查和 `git diff --check`，并确认 `git status` 没有原图或教学包文件。
