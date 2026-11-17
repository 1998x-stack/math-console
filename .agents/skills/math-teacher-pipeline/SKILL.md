---
name: math-teacher-pipeline
description: Orchestrate an image-to-verified-math-lesson workflow; use for end-to-end image, explanation, storyboard, Manim, MP4 and PPTX requests.
---

# 教师工作台总编排

## 何时触发
Orchestrate an image-to-verified-math-lesson workflow; use for end-to-end image, explanation, storyboard, Manim, MP4 and PPTX requests.

## 输入条件
- 有用户原始图片、输出工作区、学段和语言（默认高中/zh-CN）
- 确认不包含未经授权公开的学生个人信息

## 执行顺序
1. 执行 python scripts/math_console.py init --image <picture> --run workspaces/<id>；不覆盖已有 run。
2. 加载 math-image-intake 并让视觉 Agent 产出 problem.json；完成 G0。
3. 加载 math-solution 生成 solution.json、solution.md；完成 G1。
4. 将题目和解答交给**独立审校者**，加载 math-proof-audit；完成 G2。若证明存在难点或风险等级为 high，获取真人教师签核。
5. 只有 G2 pass 后，按顺序加载 math-storyboard、math-manim、math-video、math-practice-ppt。
6. 加载 math-release-qa；在验证通过后由 CLI 生成 release.json 和文件哈希。报告完成/缺失和阻塞原因。

## 输出契约
- `run.json`
- `problem.json`
- `solution.md`
- `solution.json`
- `audit.json`
- `storyboard.json`
- `storyboard.md`
- `lesson_scene.py`
- `lesson.mp4`
- `practice.json`
- `practice.pptx`
- `release.json`

## 严格门槛
不可跳过任一门槛。脚本不能替代具备视觉的 LLM、独立证明或真人签核。

## 按需加载文件
- `references/orchestration-playbook.md`：完整专业判定规则和示例。
- `scripts/run_status.py`：阶段确定性检查/执行入口。
- `assets/lesson-config.example.json`：输入输出模板；**示例不是已审核真实数据**。
- `manifest.json`：版本、依赖、输入输出和兼容元信息。

工作区相对仓库根目录，脚本引用始终以 Skill 目录为基准。失败时记录 blocker 并返回上一阶段，不写虚假的 success 文件。
