---
name: math-proof-audit
description: Independently audit multi-step math proofs, assumptions, parameter cases, counterexamples and verification reports; must run before storyboard or animation.
---

# 独立数学证明审校

## 何时触发
Independently audit multi-step math proofs, assumptions, parameter cases, counterexamples and verification reports; must run before storyboard or animation.

## 输入条件
- problem.json + solution.json + solution.md
- 审校上下文与解题上下文隔离；审校身份不得伪造

## 执行顺序
1. 独立重推或采用不同方法推导结论；从原题检查定义域、条件、量词、图形约束。
2. 逐步列出 proof obligations；检查每个 step_id、depends_on 与数学变形是否有效。
3. 使用 SymPy/数值抽样寻找反例和边界，但不要把抽样或计算机化简当成数学证明。
4. 将全部覆盖记录到 audit.json 的 checks；每项 evidence 应可复查，reviewer.independent_from_solver=true 仅在事实成立时填写。
5. 高风险证明需保留 `human_review.required=true`；默认 auto_waiver 免等待教师签字阻塞，但不能编造 `approved=true`；strict 模式要求真实教师确认后才标记已批准。
6. 运行 scripts/check_audit.py --run <dir>；若 revise/block，退回 math-solution 迭代，绝不绕开 G2。

## 输出契约
- `audit.json`

## 严格门槛
验证独立性、全部 step 覆盖与严重问题清零。默认免签不等于真实教师审核，也不能绕过独立数学审校。

## 按需加载文件
- `references/verification-matrix.md`：完整专业判定规则和示例。
- `scripts/check_audit.py`：阶段确定性检查/执行入口。
- `assets/audit.example.json`：输入输出模板；**示例不是已审核真实数据**。
- `manifest.json`：版本、依赖、输入输出和兼容元信息。

工作区相对仓库根目录，脚本引用始终以 Skill 目录为基准。失败时记录 blocker 并返回上一阶段，不写虚假的 success 文件。
