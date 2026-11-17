# Codex 本地深度迭代

- [deep-iteration.md](deep-iteration.md)：主控 Prompt，覆盖本地诊断、Agent 协同、质量门禁、真实数学题 E2E、有限回合修复和证据报告。
- [continue-iteration.md](continue-iteration.md)：下一轮基于当前真实测试状态继续修复。

## 首次运行（在 math-console 根目录）

使用 Codex CLI 的 `--image` 把真实数学题图片**直接交给模型**，不是交给脚本解析。Codex Agent 应亲自观察公式、几何示意图和小问；Python 只可在之后保存图片哈希、检查 JSON 结构或生成媒体：

```bash
IMAGE='/absolute/path/to/problem.png'
codex --sandbox workspace-write --ask-for-approval on-request --image "$IMAGE" "$(cat prompts/codex/deep-iteration.md)

INPUT_IMAGE=$IMAGE
RUN_ID=codex-local-001"
```

没准备图片时可以不传 `--image`，仅做工程框架测试，但不能宣称真实图片理解、数学审校、MP4 和 PPTX 已端到端通过。**禁止搭建 OCR 脚本**。

下一轮在同一 Codex 会话中要求：读取 prompts/codex/continue-iteration.md 并继续执行未解决问题。不要默认批准外部凭据调用、网络安装或宿主执行未知代码。

官方参考：https://learn.chatgpt.com/docs/agent-configuration/subagents 及 https://learn.chatgpt.com/docs/cli/reference

更短的直接视觉识题任务入口：[vision-first.md](vision-first.md)。
