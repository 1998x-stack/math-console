---
name: math-video
description: Render editable Manim source in a resource-limited Docker container, sync a real Chinese voiceover track and inspect final MP4 streams; use after manim stage.
---

# 隔离渲染与旁白 MP4 合成

## 何时触发
Render editable Manim source in a resource-limited Docker container, sync a real Chinese voiceover track and inspect final MP4 streams; use after manim stage.

## 必要输入/先决条件
- G4a Manim 静态检查通过
- Docker、ffmpeg、ffprobe 就绪；已获得真实旁白音频 voiceover.wav

## 严格顺序
1. 执行 docs 中给出的 Dockerfile 镜像构建，确认中文字体可加载；不要在宿主直接运行生成的 Python。
2. 由配音服务或教师实际录音生成 voiceover.wav；对照 storyboard voiceover 逐句核对，不编造 TTS 已执行状态。
3. 运行 scripts/render_docker.py --run <dir> --voiceover <file> [--build-image]；先生成 silent.mp4 预览，再验证音轨时长。
4. 若旁白与画面时长偏差过大，返回分镜或音轨编辑，不能简单靠 -shortest 截掉证明。
5. 将 real voiceover 合成到 lesson.mp4；运行 G4b 检测视频流+音频流+时长，记录渲染日志。
6. 若使用自己的 /mcp 远程渲染，依 references/render-protocol.md 配置鉴权、超时、结果回传与沙箱，同等通过 G4b。

## 输出契约
- `silent.mp4`
- `lesson.mp4`

## 不可绕过的 Gate
无声预览不得冒充最终讲解 MP4；容器沙箱不可信 Python 是硬性要求。

## 按需加载的资源
- `references/render-protocol.md`：详尽的专业准则、负例与场景设计。
- `scripts/render_docker.py`：确定性执行/验证脚本（必须按照用法调用）。
- `assets/Dockerfile`：模板或部署资源。
- `assets/voiceover.example.md`：模板或部署资源。
- `manifest.json`：独立版本号、契约与依赖记录。

> 遇到不完整的产物或不可信的数学证明，标记 blocked 并返工；禁止虚构真实渲染、人工审校或旁白生成。
