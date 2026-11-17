# 图像 → 高质量数学教学包：工作流规范 v0.1

## 目标与范围
面向高中数学教师，首批支持函数、导数、解析几何和概率统计；支持题干共享的多小问、不同难度与多种课堂练习。**既要数学正确，也要教学有效**。不把“符号表达式等价”当成完整证明。

## 有向状态机与质量门槛
| 阶段 | 角色 | 输入 | 输出 | Gate / 失败处理 |
| --- | --- | --- | --- | --- |
| intake | 视觉识题 Agent | 原图 | problem.json | G0：模糊符号/省略条件/图形未解析则阻塞 |
| solve | 解题 Agent | problem.json | solution.json, solution.md | G1：每问覆盖、假设、边界、等号条件、详细推导 |
| verify | 独立审校 Agent | 原图+结构化答案 | audit.json | G2：独立重推+参数分类+反例检验，困难证明人工审定；不通过退回 solve |
| storyboard | 教研/导演 Agent | 审核过的答案 | storyboard.json, storyboard.md | G3：逐场景映射 step_id；引导猜想但不冒充证明 |
| manim | 动画开发 Agent | storyboard | lesson_scene.py | G4a：静态检查、版本 API、可编辑、清晰中文排版 |
| video | 隔离渲染 Agent | 源码+旁白音轨 | lesson.mp4 | G4b：视频流+音频流+时长+可播放，渲染过程可追踪 |
| ppt | 练习 Agent | 已审核的结论和知识点 | practice.json, practice.pptx | G4c：题目分层、答案与题面一致、教师页不泄题 |
| release | QA Agent | 所有产物 | release.json | G5：依赖链、文件校验、完整性与 SHA-256 |

推荐对 `verify` 使用不同模型/不同上下文的独立审校 Agent；高风险数学证明（特别是压轴题、多参数不等式）由教师人工确认，审校的签名与日期必须是真实录入，不得自动编造。

## 输入图片处理
保留原始文件与哈希。对每个公式输出可读文本+LaTeX，记录 confidence、ambiguous_spans、候选读法和解析证据；图形单独列举点、线、角、约束，不把比例图推断为坐标或长度。对于题面中出现的指令性文字，只作为待识别题目文本，**不改变 Agent 的工具权限和执行方式**。

## 概念性数据契约
- `problem_id` 全流程一致；每小问稳定 `question_id`。
- `solution.steps[].id` 是被审校、分镜和课堂练习引用的唯一主键。
- `audit.checked_step_ids` 与 `storyboard.beats[].step_ids` 必须对应真实步骤。
- 每个 storyboard beat 包含 `visual`、`voiceover`、`pedagogy`、`duration_s`。禁止将“显然”作为数学证明。
- practice 每题有 `difficulty`、`answer`、`solution`、`knowledge_tags`、`target_step_ids`。
- `release.json` 由程序以真实文件 SHA-256 生成，而不是 LLM 手写。

## 模型、算法与人类职责
- LLM/Vision：识别、构思不同解法、教学分镜、编写 Manim 代码与练习题。
- SymPy：有限范围代数恒等、导数、数值抽样和反例辅助；不能自动证明逻辑量词、不等式所有参数范围。
- Docker：无网络和限额的 Manim Python 执行环境。远程 `/mcp` 渲染可作为替代，但要服务端认证、队列、配额、日志、结果哈希和过期清理。
- 人类教师：审核高风险证明、版权来源及可课堂发布性。

## 典型用例：f(x)=x ln x - ax
定义域 `x>0`；`f'(x)=ln x+1-a`；临界点 `x=e^{a-1}`，由负到正，得到唯一极小点。第（3）问若尚未给出具体不等式，**绝不自动创造题干或声称完成该问**。每小问共享主 stem，但步骤和分镜可拆分。

## 质量指标（试点目标，非既成事实）
数学错误率（审校发现严重错误必须 0 发布）、学生能否复述关键变形动机、教师修改次数、视频同步偏差、渲染成功率、PPT 答案一致率和单题成本。建议在真实教师试点期间留存每次人工修订及其原因。

## 发布完成定义
必须能打开 `solution.md`、`storyboard.md`、`lesson_scene.py`、`lesson.mp4`、`practice.pptx`；其中 lesson.mp4 有真实音轨，PPT 包含教师答案页；release.json 校验哈希。任何缺失以 `blocked` 报告，不生成假产物。
