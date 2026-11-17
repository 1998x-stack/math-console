---
name: math-manim
description: Translate an audited mathematical storyboard into editable Manim Community Python scenes with Chinese fonts, predictable timing and source mapping; use for lesson_scene.py.
---

# 可编辑 Manim 教学动画源码

## 何时触发
Translate an audited mathematical storyboard into editable Manim Community Python scenes with Chinese fonts, predictable timing and source mapping; use for lesson_scene.py.

## 必要输入/先决条件
- G3 storyboard.json + storyboard.md
- Python 3.11+、Manim Community 0.19.x 项目兼容约束

## 严格顺序
1. 按 scene_id 实现可编辑 mobject；使用有意义的变量名和函数封装，并将 beat_id/step_id 放入注释映射。
2. 使用 Text 显示中文、MathTex 显示公式；小数使用稳定格式，避免 MathTex 每帧重新编译。
3. 优先用 ValueTracker 驱动交互式演示，避免每帧创建庞大对象；每步动画与 voiceover 对齐。
4. 保留台词脚本与画面动作的对应关系；慎用 ReplaceTransform，以免丢失对象追踪。
5. 代码不包含网络、文件读写、动态 eval、shell 和执行任意代码，最终必须在隔离 Docker 运行。
6. 产出 lesson_scene.py；运行 scripts/lint_scene.py --run <dir>，但不得把静态检查当沙箱。

## 输出契约
- `lesson_scene.py`

## 不可绕过的 Gate
必须能追溯至已验证分镜；代码静态检查通过且等待沙箱真实渲染。

## 按需加载的资源
- `references/manim-engineering.md`：详尽的专业准则、负例与场景设计。
- `scripts/lint_scene.py`：确定性执行/验证脚本（必须按照用法调用）。
- `assets/lesson_scene_template.py`：模板或部署资源。
- `manifest.json`：独立版本号、契约与依赖记录。

> 遇到不完整的产物或不可信的数学证明，标记 blocked 并返工；禁止虚构真实渲染、人工审校或旁白生成。
