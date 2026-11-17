---
name: math-storyboard
description: Design step-linked Chinese math teaching storyboard, visual metaphors, duration and narration aligned to a verified solution; use only after proof audit passes.
---

# 可验证教学分镜与讲稿设计

## 何时触发
Design step-linked Chinese math teaching storyboard, visual metaphors, duration and narration aligned to a verified solution; use only after proof audit passes.

## 必要输入/先决条件
- problem.json, solution.json, solution.md, audit.json 的 G2 审校通过
- 确定学生年级、课程深度、预计视频时长

## 严格顺序
1. 建立开场问题与学习目标；每一个解题的关键动机用学生能理解的一句话表达。
2. 按照导入 → 观察 → 猜测 → 推理 → 证明 → 迁移组织 beats，且每个 beat 关联已审校的 step_ids。
3. 对每个 beat 定义视觉元素、画面动作、文字内容、旁白原句、预计 duration_s、教师追问或暂停点。
4. 用低认知负荷策略：同一时刻只强调一个数学变化；避免同时移动超过多个无关对象。
5. 写 storyboard.json 与 storyboard.md；保证所有 solution.steps 都被至少一个 beat 引用。
6. 执行 scripts/check_storyboard.py --run <dir>；不得将图形直观当作严格证明。

## 输出契约
- `storyboard.json`
- `storyboard.md`

## 不可绕过的 Gate
G2 未通过不许生成发布用分镜；所有场景与数学步骤可追溯。

## 按需加载的资源
- `references/pedagogical-storyboard.md`：详尽的专业准则、负例与场景设计。
- `scripts/check_storyboard.py`：确定性执行/验证脚本（必须按照用法调用）。
- `assets/storyboard.example.json`：模板或部署资源。
- `manifest.json`：独立版本号、契约与依赖记录。

> 遇到不完整的产物或不可信的数学证明，标记 blocked 并返工；禁止虚构真实渲染、人工审校或旁白生成。
