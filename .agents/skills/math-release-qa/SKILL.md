---
name: math-release-qa
description: Audit all math-teaching deliverables, require genuine verified solution, storyboard, editable Manim, voiced MP4 and editable PPTX, then emit hashed release report.
---

# 教学包发布质检与版本追溯

## 何时触发
Audit all math-teaching deliverables, require genuine verified solution, storyboard, editable Manim, voiced MP4 and editable PPTX, then emit hashed release report.

## 必要输入/先决条件
- G0-G4 各阶段校验通过
- 审校证据真实、音频为实际讲解内容、输入图片版权与隐私合规

## 严格顺序
1. 执行 python scripts/math_console.py status --run <dir>，确定没有 BLOCKED 阶段。
2. 对照问题、解答、audit、分镜、Manim 与 PPT 中的数学命题和标识，确保无不一致。
3. 检查 MP4 视频和音轨以及时长；抽查开场/中段/结尾真实画面，确认无裁切与公式错误。
4. 检查 PPTX 可编辑、学生题目区与教师答案区分开，答案与解析无逻辑冲突。
5. 运行 scripts/check_release.py --run <dir> --generate 通过程序生成带 SHA 的 release.json。
6. 交付时列出全部文件和未覆盖限制；任何缺失保留阻塞状态，不造假链接。

## 输出契约
- `release.json`

## 不可绕过的 Gate
只有所有强制门槛通过才能产生 release.json；发布后文件变更会使哈希校验失败。

## 按需加载的资源
- `references/quality-rubric.md`：详尽的专业准则、负例与场景设计。
- `scripts/check_release.py`：确定性执行/验证脚本（必须按照用法调用）。
- `assets/release-checklist.md`：模板或部署资源。
- `manifest.json`：独立版本号、契约与依赖记录。

> 遇到不完整的产物或不可信的数学证明，标记 blocked 并返工；禁止虚构真实渲染、人工审校或旁白生成。
