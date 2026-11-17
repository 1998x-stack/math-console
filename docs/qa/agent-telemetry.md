# Agent 调用成本、成功率和失败恢复契约

本工具统计真实已有的运行事件，**不猜测 Codex 的 Token、费用、Agent 委派行为**。需要连接实际运行时的 usage 日志才有可用的数据。

## 实际事件格式

在 Git 忽略的 `workspaces/<run-id>/reports/agent-events.jsonl` 内每行存一条真实事件。例如：

```json
{"run_id":"sample","mode":"full","agent_id":"math-solver","stage":"solve","status":"complete","context_id":"actual-context-from-runtime","duration_ms":1500,"input_tokens":1200,"output_tokens":350,"cost_usd":null,"source":"actual-provider-usage"}
```

无法从实际运行时取得的字段必须保持 null 或不提供，不得以 0 冒充真实消耗；context_id 应来自真实会话，不得编造。

## 汇总命令

```bash
python scripts/summarize_agent_usage.py --events workspaces/<run-id>/reports/agent-events.jsonl --output workspaces/<run-id>/reports/usage-summary.json
```

仅当全部事件的输入/输出 token、费用或时长都有记录时，脚本才输出相应总量；否则输出 null 和 missing_or_partial 状态。比对 full 与 slim 两种编排时必须使用同题、同一个质量门禁和独立数学评分。

建议指标：真实调用次数、失败/阻塞率、重试次数、各 Gate 返工次数、总 Token、成本、实际时延、数学通过率、有效发布率。

## 失败恢复

每次失败记录 stage、status、reason、retryable 与 source；只重跑失败阶段及受其影响的下游步骤。修改数学解答后必须重新通过 G2，不得修改 audit.verdict 伪造通过。
