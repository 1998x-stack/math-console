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
import platform
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
TEACHER_APPROVAL_FILE = "teacher-approval.json"
FORBIDDEN_IMPORTS = {"os", "sys", "subprocess", "socket", "requests", "httpx", "urllib", "shutil", "pathlib"}
FORBIDDEN_CALLS = {"eval", "exec", "compile", "open", "__import__"}
# A track whose peak stays below this level is treated as having no real narration.
SILENCE_MAX_DBFS = -50.0
# Minimum length of the written justification required to stay at risk_level=standard.
MIN_RISK_RATIONALE = 10
# G4c: student pages must never carry answers, and all three layers must exist.
STUDENT_SECTION_PREFIX = "学生练习"
ANSWER_SECTION_PREFIX = "教师答案"
DIFFICULTY_LAYERS = ("foundation", "transfer", "challenge")
# G4b: the storyboard states the intended lesson length. The renderer additionally
# checks |video - voiceover| <= 3 s; this gate catches the gross case of a storyboard
# claiming a ten-minute lesson while the shipped clip is three seconds long.
STORYBOARD_DURATION_TOLERANCE_S = 10.0
STORYBOARD_DURATION_TOLERANCE_RATIO = 0.35
AUDIO_SYNC_TOLERANCE_S = 3.0
# Gate levels: `practice` is the earlier "ready" level (structure, layers, answer
# separation) and `release` re-verifies an already published release.json.
DRAFT_STAGE = "practice"
RELEASE_STAGE = "release"
STATUS_STAGES = ("intake", "solve", "verify", "storyboard", "manim",
                 DRAFT_STAGE, "video", "ppt", RELEASE_STAGE)
CHECK_STAGES = ("intake", "solve", "verify", "storyboard", "manim",
                DRAFT_STAGE, "video", "ppt", RELEASE_STAGE, "all")

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
            ["ffprobe", "-v", "error", "-show_entries",
             "format=duration:stream=codec_type,duration",
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
    board = check_storyboard(run)
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
    # A lesson that the storyboard describes as far longer than the shipped clip has
    # not actually been produced, even though both streams exist.
    declared = sum(float(beat["duration_s"]) for beat in board["beats"])
    tolerance = max(STORYBOARD_DURATION_TOLERANCE_S,
                    STORYBOARD_DURATION_TOLERANCE_RATIO * declared)
    if abs(length - declared) > tolerance:
        fail(
            f"分镜声明的总时长 {declared:.1f}s 与实际视频 {length:.1f}s 相差 "
            f"{abs(length - declared):.1f}s（允许 {tolerance:.1f}s）：声明的讲解长度与真实成片不符"
        )
    audio_seconds = stream_duration(report, "audio")
    if audio_seconds and abs(audio_seconds - length) > max(AUDIO_SYNC_TOLERANCE_S, 0.1 * length):
        fail(f"音画不同步：音轨 {audio_seconds:.1f}s 与画面 {length:.1f}s 偏差过大")
    peak = audio_peak_dbfs(file)
    if peak < SILENCE_MAX_DBFS:
        fail(
            f"讲解视频的音轨接近静音（峰值 {peak} dBFS，阈值 {SILENCE_MAX_DBFS} dBFS）："
            "存在音频流并不等于有真实旁白，不得把无声 MP4 标记为讲解成品"
        )
    return file, length

def stream_duration(report: dict, codec_type: str):
    """Duration of the first stream of a given type, or None when unreported."""
    for stream in report.get("streams", []):
        if stream.get("codec_type") != codec_type:
            continue
        try:
            return float(stream["duration"])
        except (KeyError, TypeError, ValueError):
            return None
    return None

def pptx_pages(ppt) -> list:
    """Classify each slide as student / answer / other using its section header.

    build_slides.py writes the section name into the first text frame of every
    content slide. Requiring that declared header is what makes it possible to
    prove that an answer is *not* on a student page instead of merely probing the
    concatenation of every slide.
    """
    pages = []
    for slide in ppt.slides:
        texts = [shape.text for shape in slide.shapes if shape.has_text_frame]
        kind = "other"
        for text in texts:
            stripped = text.strip()
            if stripped.startswith(STUDENT_SECTION_PREFIX):
                kind = "student"
                break
            if stripped.startswith(ANSWER_SECTION_PREFIX):
                kind = "answer"
                break
        pages.append((kind, "\n".join(texts)))
    return pages

def check_practice(run: Path):
    """G4c, draft level: practice data and deck content, no video required yet.

    Splitting this out of check_ppt keeps "the deck is ready" separate from "the
    package may be published", which still requires the voiced MP4 at G4b.
    """
    problem, solution, _ = check_verify(run)
    practice = load_json(require(run, "practice.json"))
    schema_validate(practice, "practice.schema.json")
    if practice["problem_id"] != problem["problem_id"]:
        fail("practice.problem_id 不一致")
    unique([x["id"] for x in practice["items"]], "practice.items")
    source_ids = {x["id"] for x in solution["steps"]}
    for item in practice["items"]:
        if not item["target_step_ids"] or not set(item["target_step_ids"]).issubset(source_ids):
            fail(f"练习题 {item['id']} 引用了不存在的解答步骤")
    layers = {item["difficulty"] for item in practice["items"]}
    absent = [layer for layer in DIFFICULTY_LAYERS if layer not in layers]
    if absent:
        fail("分层练习必须包含基础/迁移/挑战三层；缺少: " + ", ".join(absent))
    ppt_path = require(run, "practice.pptx", 2048)
    try:
        from pptx import Presentation
    except ImportError:
        fail("缺少 python-pptx")
    ppt = Presentation(str(ppt_path))
    if len(ppt.slides) < len(practice["items"]) * 2 + 1:
        fail("PPT 缺少练习/答案页")
    pages = pptx_pages(ppt)
    student = "\n".join(text for kind, text in pages if kind == "student")
    teacher = "\n".join(text for kind, text in pages if kind == "answer")
    if not student:
        fail("PPTX 没有可识别的学生页：每页页首分区文本必须以「学生练习」开头")
    if not teacher:
        fail("PPTX 没有可识别的教师答案页：每页页首分区文本必须以「教师答案」开头")
    for item in practice["items"]:
        labeled = "答案：" + item["answer"]
        if item["question"] not in student:
            fail(f"PPTX 学生页丢失题面: {item['id']}")
        if labeled in student:
            fail(f"PPTX 答案泄漏到学生页: {item['id']}（学生页不得出现「答案：…」）")
        if labeled not in teacher:
            fail(f"PPTX 教师答案页丢失答案: {item['id']}")
        if len(item["answer"]) >= 6 and item["answer"] in student:
            fail(f"PPTX 学生页出现答案文本: {item['id']}")
    return ppt_path

def check_ppt(run: Path):
    """G4c, publishable level: the deck plus the voiced lesson video (G4b)."""
    ppt_path = check_practice(run)
    check_video(run)
    return ppt_path

def toolchain_report() -> dict:
    """Record the versions that produced the evidence, so it can be re-checked."""
    def first_line(command: list) -> str:
        if shutil.which(command[0]) is None:
            return "missing"
        try:
            proc = subprocess.run(command, capture_output=True, text=True, timeout=30)
        except (OSError, subprocess.SubprocessError):
            return "unavailable"
        lines = (proc.stdout or proc.stderr).strip().splitlines()
        return lines[0] if lines else "unknown"

    def package_version(name: str) -> str:
        try:
            from importlib.metadata import PackageNotFoundError, version
        except ImportError:  # pragma: no cover - Python < 3.8 is already rejected
            return "unavailable"
        try:
            return version(name)
        except PackageNotFoundError:
            return "missing"

    return {
        "python": platform.python_version(),
        "platform": platform.system(),
        "ffprobe": first_line(["ffprobe", "-version"]),
        "ffmpeg": first_line(["ffmpeg", "-version"]),
        "jsonschema": package_version("jsonschema"),
        "python-pptx": package_version("python-pptx"),
    }

def gate_evidence(run: Path) -> dict:
    """Facts each gate actually observed, so a reader can re-check the claim."""
    problem, solution, audit = check_verify(run)
    board = check_storyboard(run)
    scene = check_manim(run)
    video_file, length = check_video(run)
    practice = load_json(require(run, "practice.json"))
    try:
        from pptx import Presentation
        slides = len(Presentation(str(safe_path(run, "practice.pptx"))).slides)
    except ImportError:  # pragma: no cover - check_practice already fails first
        slides = 0
    return {
        "intake": {
            "question_ids": sorted(q["id"] for q in problem["questions"]),
            "risk_level": problem.get("risk_level", "high"),
            "ambiguities": len(problem.get("ambiguities", [])),
        },
        "solve": {
            "steps": len(solution["steps"]),
            "results": len(solution["results"]),
            "author_agent": solution["author"]["agent_id"],
            "author_context": solution["author"]["context_id"],
            "author_route": solution["author"]["route"],
        },
        "verify": {
            "reviewer_id": audit["reviewer"]["id"],
            "independent_reviewer_context": audit["reviewer"]["context_id"],
            "checks": len(audit["checks"]),
            "tested_cases": len(audit.get("tested_cases", [])),
            "human_approved": audit["human_review"]["approved"],
        },
        "storyboard": {
            "beats": len(board["beats"]),
            "declared_duration_s": sum(float(beat["duration_s"]) for beat in board["beats"]),
        },
        "manim": {"lesson_scene_sha256": digest(scene)},
        "video": {"duration_s": round(length, 3), "audio_peak_dbfs": round(audio_peak_dbfs(video_file), 2)},
        "practice": {
            "items": len(practice["items"]),
            "layers": sorted({item["difficulty"] for item in practice["items"]}),
            "slides": slides,
        },
    }

def check_release(run: Path):
    """G5: re-verify an already published release report against the current files.

    Without this, mutating a released artifact left no trace: every content gate
    still passed because none of them compares the shipped bytes to the bytes that
    were actually published.
    """
    check_ppt(run)
    report = load_json(require(run, "release.json"))
    info = load_run_meta(run)
    if report.get("run_id") != info["run_id"]:
        fail("release.json 的 run_id 与 run.json 不一致")
    if report.get("source_sha256") != info["source_sha256"]:
        fail("release.json 记录的原图哈希与 run.json 不一致")
    gate_status = report.get("gate_status")
    if not isinstance(gate_status, dict):
        fail("release.json 缺少 gate_status")
    for stage in (*STAGES, DRAFT_STAGE):
        if gate_status.get(stage) != "pass":
            fail(f"release.json 声明 {stage} 门禁未通过，不能作为发布依据")
    artifacts = report.get("artifacts")
    if not isinstance(artifacts, dict) or not artifacts:
        fail("release.json 缺少 artifacts 清单")
    unlisted = sorted(set(RELEASE_FILES) - set(artifacts))
    if unlisted:
        fail("release.json 未登记全部交付物: " + ", ".join(unlisted))
    if (run / TEACHER_APPROVAL_FILE).is_file():
        if TEACHER_APPROVAL_FILE not in artifacts:
            fail("release.json 未登记现有教师批准证据")
        check_teacher_approval(run)
    stale = []
    for name, recorded in artifacts.items():
        file = require(run, name)
        if (not isinstance(recorded, dict)
                or digest(file) != recorded.get("sha256")
                or file.stat().st_size != recorded.get("size_bytes")):
            stale.append(name)
    if stale:
        fail("release.json 已过期：" + ", ".join(sorted(stale))
             + " 在发布后被修改（哈希/大小不一致），必须重新通过门禁并重新生成 release.json")
    return report

def check_one(run: Path, stage: str):
    return {
        "intake": check_intake, "solve": check_solve, "verify": check_verify,
        "storyboard": check_storyboard, "manim": check_manim,
        "video": check_video, DRAFT_STAGE: check_practice, "ppt": check_ppt,
        RELEASE_STAGE: check_release,
    }[stage](run)

def status(run: Path):
    for stage in STATUS_STAGES:
        try:
            check_one(run, stage)
            print(f"[PASS] {stage}")
        except (GateError, OSError, ValueError, KeyError, TypeError) as exc:
            print(f"[BLOCKED] {stage}: {exc}")

def check_teacher_approval(run: Path):
    """Bind an optional user-declared package approval to exact shipped bytes.

    This validates provenance structure and hashes, not whether a person truly
    reviewed every exercise. That claim remains the human reviewer's own.
    """
    evidence = load_json(require(run, TEACHER_APPROVAL_FILE))
    info = load_run_meta(run)
    if evidence.get("run_id") != info["run_id"] or evidence.get("approved") is not True:
        fail("教师批准证据的 run_id 不匹配或未批准")
    if not evidence.get("reviewer_name") or evidence.get("approval_type") != "user_self_attestation":
        fail("教师批准证据缺少署名或声明来源")
    recorded = evidence.get("approved_artifact_sha256")
    if not isinstance(recorded, dict) or set(recorded) != set(RELEASE_FILES):
        fail("教师批准证据未覆盖全部发布产物")
    changed = [name for name in RELEASE_FILES if recorded[name] != digest(require(run, name))]
    if changed:
        fail("教师批准证据所指产物已变更: " + ", ".join(changed))
    return evidence

def do_release(run: Path):
    check_ppt(run)
    if (run / TEACHER_APPROVAL_FILE).is_file():
        check_teacher_approval(run)
    info = load_run_meta(run)
    release_files = RELEASE_FILES + ((TEACHER_APPROVAL_FILE,) if (run / TEACHER_APPROVAL_FILE).is_file() else ())
    files = {name: {"sha256": digest(require(run, name)),
                    "size_bytes": require(run, name).stat().st_size}
             for name in release_files}
    release = {
        "schema_version": "0.2.0", "run_id": info["run_id"],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "gate_status": {stage: "pass" for stage in (*STAGES, DRAFT_STAGE)},
        "source_sha256": info["source_sha256"],
        "artifacts": files,
        "toolchain": toolchain_report(),
        "gate_evidence": gate_evidence(run),
        "note": (
            "结构、媒体与交付门槛检查通过；gate_evidence 是各门禁实际观测到的事实，"
            "不代表脚本独立证明了数学命题。可用 check --stage release 复核哈希是否仍然一致。"
        ),
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
    check.add_argument("--stage", choices=CHECK_STAGES, required=True)
    args = p.parse_args()
    try:
        if args.command == "init":
            do_init(args.image, args.run)
        elif args.command == "status":
            status(args.run)
        elif args.command == "release":
            do_release(args.run)
        elif args.stage == "all":
            for stage in (*STAGES, DRAFT_STAGE):
                check_one(args.run, stage)
            # A release that already exists must still match the files on disk; otherwise
            # "all gates pass" would be printed for a stale published package.
            if (args.run / "release.json").is_file():
                check_release(args.run)
                print("[PASS] release report still matches every published artifact")
            print("[PASS] all content and draft gates（release.json 不存在时用 release 子命令生成）")
        else:
            check_one(args.run, args.stage)
            print(f"[PASS] {args.stage}")
    except (GateError, OSError, ValueError, KeyError, TypeError) as exc:
        print(f"[BLOCKED] {exc}", file=sys.stderr)
        raise SystemExit(2) from None

if __name__ == "__main__":
    main()
