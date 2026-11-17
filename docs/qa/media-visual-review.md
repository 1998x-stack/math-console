# Manim 与 PPT 视觉审阅协议

**图片含义、数学公式和视频质量必须由具备原生视觉能力的 Agent 直接查看；脚本绝不能代替看图。**

## 真实操作

1. 先完成 G2 独立数学审核，并具备真实 storyboard.json、lesson.mp4、practice.pptx。
2. 运行 `python scripts/prepare_media_review.py --run workspaces/<run-id>`；ffmpeg 仅按照分镜时长抽取 PNG 帧，创建 `media-review.json` 且初始状态必然是 pending。
3. 将 `reviews/frame_*.png` 作为图片直接提供给多模态 Agent，逐个核对 beat_id、step_ids、数学表达式、图像布局、图形正确性和证明步骤。
4. 听真实中文旁白并与分镜对照；音轨存在、峰值正常、时长吻合均不等于内容准确。
5. 用 PowerPoint / 隔离的 LibreOffice 把 PPTX 逐页呈现或导出为可见图片，让 Agent 逐页直接审查中文字体、数学公式、溢出、学生页泄题和教师页解析。
6. 真实完成后由审阅 Agent 填写 reviewer.agent_id、context_id，逐场景标记 verdict=pass 及三个检查布尔值，并写具体 notes；PPT 审阅结果填写 ppt_review.status=pass 和说明，最后把顶层 status 置为 reviewed。
7. 运行 `python scripts/prepare_media_review.py --run workspaces/<run-id> --check`，只校验截图、证据字段、文件 SHA-256 和最终状态。

## 局限

- 脚本不读数学内容，截图只是取样而非全视频内容证明；遇到动态问题应额外多帧取样或直接播放。
- 上游 MP4、分镜或 PPT 改动后，审阅证据哈希失效，必须重新审核。
- media-review.json 仍是可选的补充 QA 证据：没有该文件，G5 允许发布但将其标记为 unverified_optional；**一旦该文件存在，G5 必须检查真实审核状态、截图哈希、视频/分镜/PPT 哈希，并将 media-review.json 本身列入发布哈希清单**。未完成的 pending 审阅会阻止发布。
- 审阅者应尽量不同于动画源码作者；文件中自填 context_id 本身不证明真实独立上下文。
