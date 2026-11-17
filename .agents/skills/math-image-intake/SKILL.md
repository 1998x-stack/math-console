---
name: math-image-intake
description: Directly inspect an attached math image using the agent's native multimodal vision; understand formulas, diagrams and subquestions without OCR or image-parsing scripts.
---

# 题目图片识别与结构化录入

## 何时触发
由 Agent 自身直接观看附加的数学题图片，理解公式、图形与各小问；**禁止调用 OCR/Python/图像识别脚本生成题干**。

## 输入条件
- 原题图片、引用来源与年级
- 允许保留题干原有的简体中文与 LaTeX，不得凭空补充小问

## 执行顺序
1. **直接在 Agent 的多模态视觉上下文中查看原图**。在 Codex 中使用用户附加的图片或 CLI `--image`；先读题再构造文件。不得通过 Python、OCR、Pillow、OpenCV 或图片转文字工具先“解析”内容；这些脚本无法代替 Agent 的数学视觉理解。若子 Agent 实际无法访问图像，应由有视觉能力的主 Agent 查看并如实记录交接，不得假称子 Agent 已亲自看图。
2. 题干共享部分写入 stem；每小问分配稳定 id（如 q1、q2、q3），保留原文与 LaTeX 两种形式。
3. 列出图形几何关系；不根据示意图猜测未给出的等长、直角或比例。
4. 模糊部分填入 ambiguities（候选读法、证据、是否解决）；未确定时 resolved=false。
5. Agent **亲自**编写 problem.json（包括图片实际可见的题号、分式、指数、下标、积分限、参数范围和图形标记）；完成后才可调用 `scripts/check_problem.py --run <dir>` 做 JSON/文件完整性检查。脚本不负责视觉识别，无法判断数学符号是否看对。

## 输出契约
- `problem.json`

## 严格门槛
任何视觉理解歧义、符号不清或题面缺失不得静默推断。**G0 的语义判断属于 Agent/教师；脚本只核对结构。**

## 按需加载文件
- `references/transcription-standard.md`：完整专业判定规则和示例。
- `scripts/check_problem.py`：仅校验 JSON Schema、图片存在与哈希的辅助工具；**不读取、提取或理解题干内容**。
- `assets/problem.example.json`：输入输出模板；**示例不是已审核真实数据**。
- `manifest.json`：版本、依赖、输入输出和兼容元信息。

工作区相对仓库根目录，脚本引用始终以 Skill 目录为基准。失败时记录 blocker 并返回上一阶段，不写虚假的 success 文件。
