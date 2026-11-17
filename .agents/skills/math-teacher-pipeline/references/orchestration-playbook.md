# 编排手册：状态、重试、责任与产物

## 角色矩阵
- Conductor：安排任务、写运行日志、确认各阶段拥有真实证据；不直接给自己发独立审校许可。
- Image interpreter：逐字转录，识别数学公式与图形；区分“我看到”与“我猜测”。
- Solver：至少写出可审核推导，不省略关键变形或参数分类。
- Independent proof auditor：另一模型或隔离上下文，不预设解答正确；高风险题交人工教师。
- Lesson designer：把同一个共享题干拆成每小问不同教学动画和练习。
- Manim engineer：输出简洁可编辑 Python；保留版本、字体和画面尺寸设置。
- Renderer：负责 Docker 与音频同步；仅可执行经过授权且隔离的代码。
- QA auditor：生成可追溯、可复核、不能伪造的发布报告。

## 重试与回滚
G0 不通过：回到原图查看二次截图/高清源，保留候选读法；不要继续。G1 不通过：补齐小问、定义域与逻辑分支。G2 不通过：记录独立 reviewer 的问题列表，回退到 solve；不得微改审校报告以绕过阻塞。G3 不通过：只修改 storyboard，必要时重新寻求数学审校。Manim/渲染失败：保存原错误、有限次数重试，不能通过延迟或声称“云端已成功”替代视频。PPT 出错：核对练习正确性，再生成。

## 产物契约与依赖
运行目录由 scripts/math_console.py 管理，JSON Schemas 在 schemas/。每步至少保留输入、模型/工具版本、人工更改记录、时间和输出路径。初期 CLI 执行的是 stage gates，不负责调用第三方模型。Agent 执行认知任务后写入 JSON+Markdown，随后脚本检验结构。

## 推荐调用
```bash
python scripts/math_console.py init --image /secure/problem.png --run workspaces/2026-lesson-001
python scripts/math_console.py check --run workspaces/2026-lesson-001 --stage intake
python scripts/math_console.py check --run workspaces/2026-lesson-001 --stage solve
python scripts/math_console.py check --run workspaces/2026-lesson-001 --stage verify
python scripts/math_console.py status --run workspaces/2026-lesson-001
python scripts/math_console.py release --run workspaces/2026-lesson-001
```

## 发布定义
单个成功消息不足以证明交付。需要 solution.md、storyboard.md、lesson_scene.py、带音轨 lesson.mp4、可编辑 practice.pptx 和真实生成的 release.json；发布检查必须通过。
