#!/usr/bin/env python3
"""Math Console lesson-package state machine (Python 3.11+).

Image understanding belongs exclusively to a multimodal Agent; this script never
extracts mathematical text, diagrams or meaning from an image.
This validates structure and artifact integrity, NOT mathematical truth.
Independent mathematical review is a separate mandatory checkpoint.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STAGES = ("intake", "solve", "verify", "storyboard", "manim", "video", "ppt")
SCHEMAS = {
    "intake": ("problem.json", "problem.schema.json"),
    "solve": ("solution.json", "solution.schema.json"),
    "verify": ("audit.json", "audit.schema.json"),
    "storyboard": ("storyboard.json", "storyboard.schema.json"),
    "ppt": ("practice.json", "practice.schema.json"),
}
RELEASE_FILES = (
    "problem.json", "solution.json", "solution.md", "audit.json",
    "storyboard.json", "storyboard.md", "lesson_scene.py",
    "lesson.mp4", "practice.json", "practice.pptx",
)
FORBIDDEN_IMPORTS = {"os", "sys", "subprocess", "socket", "requests", "httpx", "urllib", "shutil", "pathlib"}
FORBIDDEN_CALLS = {"eval", "exec", "compile", "open", "__import__"}
# A track whose peak stays below this level is treated as having no real narration.
SILENCE_MAX_DBFS = -50.0
# Minimum length of the written justification required to stay at risk_level=standard.
MIN_RISK_RATIONALE = 10

class GateError(RuntimeError):
    pass

def fail(msg: str) -> None:
    raise GateError(msg)

def load_json(file: Path) -> dict:
    if not file.is_file():
        fail(f"缺少文件: {file}")
    try:
        data = json.loads(file.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        fail(f"无法读取 JSON {file}: {exc}")
    if not isinstance(data, dict):
        fail(f"JSON 顶层必须为对象: {file}")
    return data

def digest(file: Path) -> str:
    sha = hashlib.sha256()
    with file.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            sha.update(chunk)
    return sha.hexdigest()

def safe_path(run: Path, relative: str) -> Path:
    base = run.resolve()
    file = (run / relative).resolve()
    if not file.is_relative_to(base):
        fail(f"非法路径（越过工作区）: {relative}")
    return file

def schema_validate(data: dict, schema_file: str) -> None:
    try:
        from jsonschema import Draft202012Validator
    except ImportError as exc:
        fail("缺少 jsonschema；请先运行 pip install -r requirements-workbench.txt")
    schema = load_json(ROOT / "schemas" / schema_file)
    errors = sorted(Draft202012Validator(schema).iter_errors(data), key=lambda err: list(map(str, err.path)))
    if errors:
        err = errors[0]
        fail(f"{schema_file}: {'/'.join(map(str, err.path)) or '<root>'}: {err.message}")

def require(run: Path, name: str, min_size: int = 1) -> Path:
    file = safe_path(run, name)
    if not file.is_file() or file.stat().st_size < min_size:
        fail(f"文件缺失/空文件: {file}")
    return file

def unique(values, name: str) -> None:
    if len(values) != len(set(values)):
        fail(f"{name} 存在重复 ID")

def load_run_meta(run: Path) -> dict:
    """run.json is not schema-validated, so missing fields must fail loudly and cleanly."""
    info = load_json(require(run, "run.json"))
    for field in ("run_id", "source_image", "source_sha256"):
        if not info.get(field):
            fail(f"run.json 缺少必需字段 {field}；请用 math_console.py init 重新初始化该工作区")
    return info


def check_intake(run: Path):
    problem = load_json(require(run, "problem.json"))
    schema_validate(problem, "problem.schema.json")
    if not problem["source"]["image_paths"]:
        fail("题目缺少原图路径")
    for relative in problem["source"]["image_paths"]:
        source = require(run, relative, 100)
        if source.suffix.lower() not in (".jpg", ".jpeg", ".png", ".webp", ".bmp"):
            fail(f"不支持的图片格式: {source}")
    run_info = load_run_meta(run)
    first = safe_path(run, problem["source"]["image_paths"][0])
    if digest(first) != run_info["source_sha256"]:
        fail("原图 SHA-256 与 run.json 不符")
    if problem["source"].get("sha256") and problem["source"]["sha256"] != digest(first):
        fail("problem.json 声称的原图哈希不符")
    unique([q["id"] for q in problem["questions"]], "question")
    if any(not x["resolved"] or not x.get("resolution") for x in problem["ambiguities"]):
        fail("存在未解决的视觉读题/题意歧义：必须先由 Agent 或教师核查")
    return problem

def check_step_graph(steps: list) -> None:
    """Reject dependency cycles and forward references between solution steps.

    Without this, a solution could claim s1 <- s2 <- s1 and still be "complete".
    Cycles are reported first because they are the more fundamental defect.
    """
    ids = [step["id"] for step in steps]
    index = {sid: i for i, sid in enumerate(ids)}
    graph = {step["id"]: [dep for dep in step["depends_on"] if dep in index]
             for step in steps}
    WHITE, GREY, BLACK = 0, 1, 2
    colour = dict.fromkeys(ids, WHITE)

    def visit(node: str, path: list) -> None:
        colour[node] = GREY
        for dep in graph[node]:
            if colour[dep] == GREY:
                fail(f"解答步骤依赖存在循环：{' -> '.join(path + [dep])}；推导顺序不成立")
            if colour[dep] == WHITE:
                visit(dep, path + [dep])
        colour[node] = BLACK

    for sid in ids:
        if colour[sid] == WHITE:
            visit(sid, [sid])

    for step in steps:
        for dep in step["depends_on"]:
            if index[dep] >= index[step["id"]]:
                fail(
                    f"依赖必须先于使用：步骤 {step['id']} 依赖 {dep}，"
                    f"但 {dep} 未在它之前给出；请按拓扑顺序排列步骤"
                )


def check_solve(run: Path):
    problem = check_intake(run)
    solution = load_json(require(run, "solution.json"))
    schema_validate(solution, "solution.schema.json")
    require(run, "solution.md", 80)
    if solution["problem_id"] != problem["problem_id"]:
        fail("solution.problem_id 与题目不一致")
    questions = {q["id"] for q in problem["questions"]}
    results = [r["question_id"] for r in solution["results"]]
    unique(results, "solution.results")
    if set(results) != questions:
        fail(f"没有覆盖全部小问：需要 {sorted(questions)}，得到 {results}")
    steps = solution["steps"]
    ids = [s["id"] for s in steps]
    unique(ids, "solution.steps")
    if not all(s["question_id"] in questions and s["depends_on"] is not None for s in steps):
        fail("解答步骤引用不存在的小问")
    for step in steps:
        if step["id"] in step["depends_on"]:
            fail(f"步骤自引用: {step['id']}")
        if not set(step["depends_on"]).issubset(set(ids)):
            fail(f"步骤依赖不存在: {step['id']}")
    if not questions.issubset({s["question_id"] for s in steps}):
        fail("至少一个小问没有逐步解答")
    check_step_graph(steps)
    return problem, solution

def check_verify(run: Path):
    problem, solution = check_solve(run)
    audit = load_json(require(run, "audit.json"))
    schema_validate(audit, "audit.schema.json")
    if audit["problem_id"] != problem["problem_id"]:
        fail("audit.problem_id 不一致")
    reviewer = audit["reviewer"]
    if audit["verdict"] != "pass" or not reviewer["independent_from_solver"] or any(not c["passed"] for c in audit["checks"]):
        fail("独立审校未通过，必须返工")
    if audit.get("unresolved"):
        fail("审校仍有未解决的证明义务")
    # Independence is more than a self-asserted flag: the author and the reviewer
    # must be recorded as different agents working in different contexts.
    author = solution["author"]
    if reviewer["context_id"] == author["context_id"]:
        fail("独立审校不成立：审校者与解题者使用同一 context_id，属于同一上下文自我审校")
    if reviewer["id"] == author["agent_id"]:
        fail("独立审校不成立：reviewer.id 等于 solution.author.agent_id，属于同一 Agent 自我审校")
    step_ids = {s["id"] for s in solution["steps"]}
    checked_ids = {sid for check in audit["checks"] for sid in check["step_ids"]}
    if not checked_ids.issubset(step_ids) or not step_ids.issubset(checked_ids):
        fail("审校必须覆盖全部解题步骤并引用真实 step_id")
    # Risk must not be downgraded by whoever wrote the solution.
    risk = problem.get("risk_level", "high")
    proof_steps = sorted(s["id"] for s in solution["steps"] if s.get("proof_obligation"))
    if proof_steps and risk != "high":
        fail(f"步骤 {proof_steps} 标记了证明义务，必须按高风险处理（risk_level=high），禁止降级以跳过教师签核")
    if risk == "standard" and len(problem.get("risk_rationale", "").strip()) < MIN_RISK_RATIONALE:
        fail("risk_level=standard 必须提供 risk_rationale（≥10 字）说明为何不属高风险，防止自行降级")
    human = audit["human_review"]
    if risk == "high" and (not human["required"] or not human["approved"]):
        fail("高风险数学证明必须有教师人工签核")
    if human["required"] and (
        not human["approved"] or not human.get("reviewer_name") or not human.get("reviewed_at")
    ):
        fail("教师签核缺少真实姓名、时间或批准状态")
    return problem, solution, audit

def check_storyboard(run: Path):
    problem, solution, audit = check_verify(run)
    board = load_json(require(run, "storyboard.json"))
    schema_validate(board, "storyboard.schema.json")
    require(run, "storyboard.md", 50)
    if board["problem_id"] != problem["problem_id"]:
        fail("storyboard.problem_id 不一致")
    step_ids = {s["id"] for s in solution["steps"]}
    beat_ids = [beat["id"] for beat in board["beats"]]
    unique(beat_ids, "storyboard.beats")
    covered = {sid for beat in board["beats"] for sid in beat["step_ids"]}
    if not covered or not covered.issubset(step_ids):
        fail("教学分镜引用不存在的推导步骤或没有任何数学步骤")
    if not step_ids.issubset(covered):
        fail("部分解题步骤未在分镜中体现")
    return board

def check_manim(run: Path):
    check_storyboard(run)
    file = require(run, "lesson_scene.py", 100)
    try:
        tree = ast.parse(file.read_text(encoding="utf-8"))
    except SyntaxError as exc:
        fail(f"Manim 源码存在 Python 语法错误：{exc}")
    classes = {node.name for node in tree.body if isinstance(node, ast.ClassDef)}
    if "LessonScene" not in classes:
        fail("必须定义可编辑的 LessonScene 类")
    if not any(isinstance(node, (ast.Import, ast.ImportFrom)) and
               ((isinstance(node, ast.ImportFrom) and node.module == "manim") or
                (isinstance(node, ast.Import) and any(a.name == "manim" for a in node.names)))
               for node in tree.body):
        fail("lesson_scene.py 未导入 manim")
    for node in ast.walk(tree):
        if isinstance(node, ast.Import) and any(a.name.split(".")[0] in FORBIDDEN_IMPORTS for a in node.names):
            fail("Manim 源码包含禁止的模块导入")
        if isinstance(node, ast.ImportFrom) and (node.module or "").split(".")[0] in FORBIDDEN_IMPORTS:
            fail("Manim 源码包含禁止的模块导入")
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in FORBIDDEN_CALLS:
            fail("Manim 源码包含禁止的调用")
    # Static lint is NEVER a security sandbox. Render only in isolation.
    return file

def ffprobe(file: Path) -> dict:
    if shutil.which("ffprobe") is None:
        fail("缺少 ffprobe，无法确认 MP4 的真实音视频轨道")
    try:
        proc = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type",
             "-of", "json", str(file)], capture_output=True, text=True, timeout=30, check=True
        )
        return json.loads(proc.stdout)
    except (subprocess.SubprocessError, ValueError) as exc:
        fail(f"ffprobe 检测失败: {exc}")

def audio_peak_dbfs(file: Path) -> float:
    """Measure the peak level of the first audio stream via ffmpeg volumedetect.

    ffprobe only proves that an audio *stream* exists; it cannot tell a real
    Chinese voiceover from an anullsrc placeholder. AGENTS.md forbids shipping a
    silent MP4 as a finished lesson, so the level must be measured, not assumed.
    """
    if shutil.which("ffmpeg") is None:
        fail("缺少 ffmpeg，无法确认旁白音轨是否为静音")
    try:
        proc = subprocess.run(
            ["ffmpeg", "-hide_banner", "-nostats", "-i", str(file),
             "-map", "0:a:0", "-af", "volumedetect", "-f", "null", "-"],
            capture_output=True, text=True, timeout=120,
        )
    except subprocess.SubprocessError as exc:
        fail(f"音轨电平检测失败: {exc}")
    match = re.search(r"max_volume:\s*(-?[\d.]+|-inf)\s*dB", proc.stderr)
    if not match:
        fail(f"无法测量旁白音轨电平: {proc.stderr.strip()[-300:]}")
    raw = match.group(1)
    return float("-inf") if raw == "-inf" else float(raw)


def check_video(run: Path):
    check_manim(run)
    file = require(run, "lesson.mp4", 1024)
    report = ffprobe(file)
    kinds = {x.get("codec_type") for x in report.get("streams", [])}
    if not {"video", "audio"}.issubset(kinds):
        fail("讲解视频必须同时存在视频流和实际旁白音频流")
    try:
        length = float(report["format"]["duration"])
    except (KeyError, TypeError, ValueError):
        fail("MP4 不包含可用时长")
    if not 1 < length < 7200:
        fail("MP4 时长异常")
    peak = audio_peak_dbfs(file)
    if peak < SILENCE_MAX_DBFS:
        fail(
            f"讲解视频的音轨接近静音（峰值 {peak} dBFS，阈值 {SILENCE_MAX_DBFS} dBFS）："
            "存在音频流并不等于有真实旁白，不得把无声 MP4 标记为讲解成品"
        )
    return file, length

def check_ppt(run: Path):
    check_video(run)
    practice = load_json(require(run, "practice.json"))
    schema_validate(practice, "practice.schema.json")
    problem, solution, _ = check_verify(run)
    if practice["problem_id"] != problem["problem_id"]:
        fail("practice.problem_id 不一致")
    unique([x["id"] for x in practice["items"]], "practice.items")
    source_ids = {x["id"] for x in solution["steps"]}
    for item in practice["items"]:
        if not set(item["target_step_ids"]).issubset(source_ids):
            fail(f"练习题 {item['id']} 引用了不存在的解答步骤")
    ppt_path = require(run, "practice.pptx", 2048)
    try:
        from pptx import Presentation
    except ImportError:
        fail("缺少 python-pptx")
    ppt = Presentation(str(ppt_path))
    if len(ppt.slides) < len(practice["items"]) * 2 + 1:
        fail("PPT 缺少练习/答案页")
    combined = "\n".join(shape.text for slide in ppt.slides for shape in slide.shapes if shape.has_text_frame)
    for item in practice["items"]:
        if item["question"] not in combined or item["answer"] not in combined:
            fail(f"PPT 丢失题面或答案: {item['id']}")
    return ppt_path

def check_one(run: Path, stage: str):
    return {
        "intake": check_intake, "solve": check_solve, "verify": check_verify,
        "storyboard": check_storyboard, "manim": check_manim,
        "video": check_video, "ppt": check_ppt
    }[stage](run)

def status(run: Path):
    for stage in STAGES:
        try:
            check_one(run, stage)
            print(f"[PASS] {stage}")
        except (GateError, OSError, ValueError) as exc:
            print(f"[BLOCKED] {stage}: {exc}")

def do_release(run: Path):
    check_ppt(run)
    info = load_run_meta(run)
    files = {name: {"sha256": digest(require(run, name)),
                    "size_bytes": require(run, name).stat().st_size}
             for name in RELEASE_FILES}
    release = {
        "schema_version": "0.1.0", "run_id": info["run_id"],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "gate_status": {stage: "pass" for stage in STAGES},
        "source_sha256": info["source_sha256"],
        "artifacts": files,
        "note": "结构、媒体与交付门槛检查通过；不代表脚本独立证明了数学命题。"
    }
    (run / "release.json").write_text(json.dumps(release, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[RELEASE] {run / 'release.json'}")
    return release

def do_init(image: Path, run: Path):
    if run.exists() and any(run.iterdir()):
        fail("工作区已存在且不为空，禁止覆盖：请选新 --run 路径")
    if image.suffix.lower() not in (".png", ".jpg", ".jpeg", ".webp", ".bmp"):
        fail("输入不是支持的图片扩展名")
    if not image.is_file() or image.stat().st_size > 20 * 1024 * 1024:
        fail("原图不存在，或大于 20 MB")
    try:
        from PIL import Image
        with Image.open(image) as im:
            im.verify()
    except (ImportError, OSError, ValueError) as exc:
        fail(f"图片内容校验失败: {exc}")
    (run / "input").mkdir(parents=True, exist_ok=True)
    target = run / "input" / ("problem" + image.suffix.lower())
    shutil.copyfile(image, target)
    info = {"schema_version": "0.1.0", "run_id": run.name,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "source_image": str(target.relative_to(run)),
            "source_sha256": digest(target),
            "phase": "awaiting_visual_transcription"}
    (run / "run.json").write_text(json.dumps(info, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[INIT] {run}\n原图保存在 {target}\n请由具备视觉能力的 Agent 录入 problem.json；随后 check --stage intake")

def main():
    if sys.version_info < (3, 11):
        print(
            "需要 Python 3.11 或更高版本（当前 %d.%d）。本工作台按 CI 的 Python 3.12 验证；"
            "请使用 python3.12 scripts/math_console.py 运行。" % sys.version_info[:2],
            file=sys.stderr,
        )
        raise SystemExit(2)
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)
    init = sub.add_parser("init", help="Initialize a run from a problem image")
    init.add_argument("--image", required=True, type=Path)
    init.add_argument("--run", required=True, type=Path)
    for cmd in ("status", "release"):
        sub.add_parser(cmd).add_argument("--run", required=True, type=Path)
    check = sub.add_parser("check", help="Validate a specific stage or all stages")
    check.add_argument("--run", required=True, type=Path)
    check.add_argument("--stage", choices=STAGES + ("all",), required=True)
    args = p.parse_args()
    try:
        if args.command == "init":
            do_init(args.image, args.run)
        elif args.command == "status":
            status(args.run)
        elif args.command == "release":
            do_release(args.run)
        elif args.stage == "all":
            for stage in STAGES:
                check_one(args.run, stage)
            print("[PASS] all stages")
        else:
            check_one(args.run, args.stage)
            print(f"[PASS] {args.stage}")
    except (GateError, OSError, ValueError, KeyError, TypeError) as exc:
        print(f"[BLOCKED] {exc}", file=sys.stderr)
        raise SystemExit(2) from None

if __name__ == "__main__":
    main()
