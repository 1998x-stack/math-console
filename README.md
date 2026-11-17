# Math Console

面向 AI 数学教育的产品规划、数学知识资产与教学工程方案。

## AI 数学教育三产品规划（2026 年 11 月）

这三个方向共享数学知识、题目、教学分镜、验证机制与学习反馈数据，但面向不同的产品阶段。

| 方向 | 面向用户 | 核心能力 | PDF | 可编辑源文件 |
| --- | --- | --- | --- | --- |
| **A · AI 数学教师工作台** | 教师、教研团队、内容创作者 | 题目解析、数学审校、分镜、Manim 动画与课件 | [PDF · 10 页](docs/product-plans/AI_Math_A_Teacher_Workbench_2026.pdf) | [HTML](docs/product-plans/AI_Math_A_Teacher_Workbench_2026.html) |
| **B · AI 数学交互实验室** | 学生、教师和课堂 | 参数实验、图形探索、预测与验证、课堂活动 | [PDF · 10 页](docs/product-plans/AI_Math_B_Interactive_Lab_2026.pdf) | [HTML](docs/product-plans/AI_Math_B_Interactive_Lab_2026.html) |
| **C · AI 个性化数学导师** | 学生和教师 | 错因识别、分层提示、知识诊断、学习效果评价 | [PDF · 12 页](docs/product-plans/AI_Math_C_Personalized_Tutor_2026.pdf) | [HTML](docs/product-plans/AI_Math_C_Personalized_Tutor_2026.html) |

**建议建设顺序：** A 验证教师真实需求 → B 验证交互式教学效果 → C 在教学效果与隐私安全通过验证后发展个性化辅导。

### 文档涵盖内容

- 产品定位、用户画像、使用场景、核心流程、功能需求与 MVP 范围
- 典型数学教学案例、技术架构、与 Manim / 数学验证引擎的集成思路
- 数据模型、工程交付、质量与可解释性要求
- 90 天行动计划、12 个月路线图、预算情景与商业化边界
- 教学研究、合规风险以及三种产品之间的协同接口

### PDF 构建

三份 HTML 是可版本化的文档源文件。修改对应的 HTML 后，GitHub Actions 会使用 WeasyPrint 与中文字体重新渲染 PDF，并提交到相同目录。

自动构建配置：[`.github/workflows/build-product-plan-pdfs.yml`](.github/workflows/build-product-plan-pdfs.yml)。

本地重新渲染（安装中文字体后）：

```bash
python -m pip install weasyprint==68.0
python - <<'PY'
from pathlib import Path
from weasyprint import HTML

for source in Path("docs/product-plans").glob("AI_Math_*.html"):
    dest = source.with_suffix(".pdf")
    HTML(filename=str(source), base_url=str(source.parent)).write_pdf(str(dest))
    print(dest)
PY
```

> **说明：** 报告为规划草案。预算、定价、用户数量、实施进度和增长目标均为待验证的情景假设，不应直接视为市场事实或产品承诺。
