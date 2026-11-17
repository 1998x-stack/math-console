---
name: math-image-intake
description: Transcribe a mathematics problem image with exact LaTeX, subquestion IDs, diagrams and ambiguity tracking; use before attempting any solution.
---

# 题目图片识别与结构化录入

## 何时触发
Transcribe a mathematics problem image with exact LaTeX, subquestion IDs, diagrams and ambiguity tracking; use before attempting any solution.

## 输入条件
- 原题图片、引用来源与年级
- 允许保留题干原有的简体中文与 LaTeX，不得凭空补充小问

## 执行顺序
1. 用具备视觉能力的模型阅读原图；独立核查题号、分式、指数、下标、积分限、参数范围及几何图的标记。
2. 题干共享部分写入 stem；每小问分配稳定 id（如 q1、q2、q3），保留原文与 LaTeX 两种形式。
3. 列出图形几何关系；不根据示意图猜测未给出的等长、直角或比例。
4. 模糊部分填入 ambiguities（候选读法、证据、是否解决）；未确定时 resolved=false。
5. 写入 problem.json 后执行 scripts/check_problem.py --run <dir>；阻塞时联系来源图片确认。

## 输出契约
- `problem.json`

## 严格门槛
任何 OCR 模糊、符号歧义或题面缺失不得静默推断。

## 按需加载文件
- `references/transcription-standard.md`：完整专业判定规则和示例。
- `scripts/check_problem.py`：阶段确定性检查/执行入口。
- `assets/problem.example.json`：输入输出模板；**示例不是已审核真实数据**。
- `manifest.json`：版本、依赖、输入输出和兼容元信息。

工作区相对仓库根目录，脚本引用始终以 Skill 目录为基准。失败时记录 blocker 并返回上一阶段，不写虚假的 success 文件。
