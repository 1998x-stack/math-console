# 视频渲染与旁白同步协议

## Docker 本地渲染
```bash
docker build -f .agents/skills/math-video/assets/Dockerfile -t math-console/manim-zh:0.1.0 .
python .agents/skills/math-video/scripts/render_docker.py \
  --run workspaces/demo --voiceover workspaces/demo/voiceover.wav
python scripts/math_console.py check --run workspaces/demo --stage video
```

脚本在 Docker 中使用只读源码挂载、无网络、read-only 根文件系统、不可提权、内存 CPU PID 与超时限制。输出目录可写以存放视频；镜像中的字体为 Noto CJK。初期可用低质量 ql 快速检查，正式发布再按项目成本提升质量。

## 声音生产
- Agent 由 storyboard.json 的 voiceover 文本编排完整讲解音频。TTS 模型、服务、授权与调用费用由部署方指定；**本 Skill 不自动提供付费语音服务**。
- 必须有可播放的 WAV/MP3 声音文件；声音必须对应已审核的讲稿，中文数学公式要读对。
- 约束：音频与视频时长误差超过允许偏差必须退回修改；临时静音和伪造音轨不算通过。
- 字幕轨（SRT/ASS）可以后续补充，若声明含字幕必须检查该文件；当前 v0.1 默认只要求中文旁白。

## 自建 MCP 渲染接口建议（契约，不是仓库已部署事实）
- 工具 `render_manim(scene_source, scene_name, quality, request_id)`。
- 工具 `get_render_status(job_id)`。
- 工具 `download_artifact(job_id, artifact_type)`。
- HTTP `/mcp` 提供经过令牌认证的 MCP 传输；不能假设“上传文件 HTTP”与 MCP 协议自动等价。
- 服务端严格校验上传大小、源代码白名单并 Docker 隔离，按 job_id 限配额/并发/时长；下载 URL 过期，核对 SHA-256；返回 stderr/stdout 但不得泄露系统秘密。
- 取消或失败要保留结构化错误码；禁止自动将失败 job 标记为成功。

## 视频检查
检查 `ffprobe` 真实流：video+audio，duration >1s 且不过长；核对分镜 voiceover 口述与画面节奏。MP4 没有音轨只能叫预览，不能叫完整讲解成品。
