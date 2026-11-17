---
name: math-practice-ppt
description: Create an editable classroom practice PPTX with foundation, transfer and challenge questions plus separate teacher answer slides; use after the verified lesson.
---

# 分层课堂练习 PPTX 生产

## 何时触发
Create an editable classroom practice PPTX with foundation, transfer and challenge questions plus separate teacher answer slides; use after the verified lesson.

## 必要输入/先决条件
- G2 数学审校已完成；视频真实渲染后再做最终发布质检
- 练习题需重新校验正确性，不得因为来自模型就直接相信

## 严格顺序
1. 围绕本题的知识点、关键误区和逐步能力目标设计至少三道练习（基础、迁移、挑战）。
2. 每题提供题目、标准答案、可复核解析、目标 step_ids、预估完成分钟数和教师提示。
3. 教师独立审核新练习的正确性及其答案；若引入新不等式或新定理必须重新审校。
4. 编写 practice.json；参考 assets/practice.example.json 的 JSON 契约。
5. 运行 scripts/build_slides.py --run <dir>，生成真正可编辑的 practice.pptx（文字与形状不是截图）。
6. 运行 python scripts/math_console.py check --stage ppt；交付分开的题面页和教师答案页。

## 输出契约
- `practice.json`
- `practice.pptx`

## 不可绕过的 Gate
题目与答案分隔，全部练习有可复核解析；PPTX 内文字可编辑。

## 按需加载的资源
- `references/assessment-design.md`：详尽的专业准则、负例与场景设计。
- `scripts/build_slides.py`：确定性执行/验证脚本（必须按照用法调用）。
- `assets/practice.example.json`：模板或部署资源。
- `manifest.json`：独立版本号、契约与依赖记录。

> 遇到不完整的产物或不可信的数学证明，标记 blocked 并返工；禁止虚构真实渲染、人工审校或旁白生成。
