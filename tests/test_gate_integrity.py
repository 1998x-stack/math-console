"""Regression tests for gate integrity holes found by adversarial review.

Each test here exists because the gate previously accepted evidence that it
could not actually justify. Structural checks still do NOT prove mathematical
truth; they only stop the gate from *claiming* more than it verified.
"""
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import math_console as mc  # noqa: E402

HAVE_FFMPEG = shutil.which("ffmpeg") is not None and shutil.which("ffprobe") is not None


def find_legacy_interpreter():
    """Return a Python < 3.11 executable path, or None."""
    candidates = [shutil.which(name) for name in ("python3.9", "python3.10", "/usr/bin/python3")]
    if sys.platform == "darwin":
        candidates.append("/usr/bin/python3")
    for path in candidates:
        if not path or not Path(path).exists():
            continue
        probe = subprocess.run([path, "-c", "import sys;print(sys.version_info[0],sys.version_info[1])"],
                               capture_output=True, text=True)
        parts = probe.stdout.split()
        if len(parts) == 2 and (int(parts[0]), int(parts[1])) < (3, 11):
            return path
    return None


def build_run(base: Path, *, risk_level="standard", steps=None, author=None,
              reviewer=None, proof_obligation=False) -> Path:
    """Create a workspace valid up to the verify gate, with knobs for abuse cases."""
    from PIL import Image

    img = base / "source.png"
    Image.new("RGB", (128, 128), (255, 255, 255)).save(img)
    run = base / "run"
    mc.do_init(img, run)

    problem = {
        "schema_version": "0.1.0", "problem_id": "t-1",
        "source": {"image_paths": ["input/problem.png"], "language": "zh-CN"},
        "stem": {"text": "求 f(x)=x² 的导数", "latex": "f(x)=x^2"},
        "questions": [{"id": "q1", "text": "求导", "latex": "f'(x)"}],
        "ambiguities": [], "knowledge_tags": ["导数"], "risk_level": risk_level,
        "risk_rationale": "本题为单步幂函数求导，不涉及全称命题或参数分支讨论。",
    }
    (run / "problem.json").write_text(json.dumps(problem, ensure_ascii=False), encoding="utf-8")

    default_steps = [{
        "id": "s1", "question_id": "q1", "claim": "求导", "latex": "2x",
        "reason": "幂函数求导法则", "depends_on": [], "proof_obligation": proof_obligation,
    }]
    solution = {
        "schema_version": "0.2.0", "problem_id": "t-1",
        "author": author if author is not None else {
            "agent_id": "math-solver", "context_id": "ctx-solver-1",
            "route": "链式法则与定义法复核",
        },
        "assumptions": ["x 为实数"],
        "steps": default_steps if steps is None else steps,
        "results": [{"question_id": "q1", "conclusion": "导数为 2x", "latex": "2x"}],
    }
    (run / "solution.json").write_text(json.dumps(solution, ensure_ascii=False), encoding="utf-8")
    (run / "solution.md").write_text("# 解题\n\n" + "使用幂函数求导法则。\n" * 12, encoding="utf-8")

    audit = {
        "schema_version": "0.2.0", "problem_id": "t-1", "verdict": "pass",
        "reviewer": reviewer if reviewer is not None else {
            "id": "math-proof-auditor", "role": "independent_agent",
            "independent_from_solver": True, "context_id": "ctx-auditor-1",
        },
        "independent_method": "用导数定义独立重推 (x+h)^2 的极限，不参考原解答。",
        "checks": [{"id": "c1", "passed": True, "evidence": "极限展开 (x+h)^2",
                    "step_ids": ["s1"]}],
        "tested_cases": [],
        "human_review": (
            {"required": True, "approved": True, "reviewer_name": "王老师",
             "reviewed_at": "2026-01-01T00:00:00Z"}
            if risk_level == "high" else {"required": False, "approved": False}
        ),
    }
    (run / "audit.json").write_text(json.dumps(audit, ensure_ascii=False), encoding="utf-8")
    return run


def extend_to_manim(run: Path) -> Path:
    board = {
        "schema_version": "0.1.0", "problem_id": "t-1", "lesson_title": "导数入门",
        "learning_objectives": ["理解幂函数求导法则"],
        "beats": [{"id": "b1", "step_ids": ["s1"], "visual": "画出抛物线",
                   "voiceover": "观察切线斜率", "pedagogy": "从几何直觉到计算",
                   "duration_s": 9}],
    }
    (run / "storyboard.json").write_text(json.dumps(board, ensure_ascii=False), encoding="utf-8")
    (run / "storyboard.md").write_text("# 教学分镜\n\n" + "解释导数几何意义。\n" * 8,
                                       encoding="utf-8")
    (run / "lesson_scene.py").write_text(
        "from manim import *\n\n\nclass LessonScene(Scene):\n"
        "    def construct(self):\n        self.wait(1)\n" + "# padding\n" * 20,
        encoding="utf-8")
    return run


def make_mp4(run: Path, *, silent: bool) -> None:
    audio = "anullsrc=r=44100:cl=mono" if silent else "sine=frequency=440:duration=3"
    cmd = [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-f", "lavfi", "-i", audio,
        "-f", "lavfi", "-i", "color=c=black:s=64x64:d=3",
        "-shortest", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac",
        str(run / "lesson.mp4"),
    ]
    subprocess.run(cmd, check=True, capture_output=True)


class GateIntegrityTest(unittest.TestCase):
    # --- D1: dependency graph was never checked for cycles or ordering ---
    def test_dependency_cycle_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            run = build_run(base, steps=[
                {"id": "s1", "question_id": "q1", "claim": "a", "latex": "a",
                 "reason": "r1", "depends_on": ["s2"]},
                {"id": "s2", "question_id": "q1", "claim": "b", "latex": "b",
                 "reason": "r2", "depends_on": ["s1"]},
            ])
            with self.assertRaises(mc.GateError) as ctx:
                mc.check_solve(run)
            self.assertIn("循环", str(ctx.exception))

    def test_forward_dependency_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = build_run(Path(tmp), steps=[
                {"id": "s1", "question_id": "q1", "claim": "a", "latex": "a",
                 "reason": "r1", "depends_on": ["s2"]},
                {"id": "s2", "question_id": "q1", "claim": "b", "latex": "b",
                 "reason": "r2", "depends_on": []},
            ])
            with self.assertRaises(mc.GateError) as ctx:
                mc.check_solve(run)
            self.assertIn("先于", str(ctx.exception))

    # --- D3: independence was a self-asserted boolean ---
    def test_solution_must_declare_author_identity(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = build_run(Path(tmp), author={"agent_id": "math-solver"})
            with self.assertRaises(mc.GateError):
                mc.check_solve(run)

    def test_self_audit_in_same_context_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = build_run(
                Path(tmp),
                author={"agent_id": "math-solver", "context_id": "ctx-1", "route": "导数定义法"},
                reviewer={"id": "math-proof-auditor", "role": "independent_agent",
                          "independent_from_solver": True, "context_id": "ctx-1"},
            )
            with self.assertRaises(mc.GateError) as ctx:
                mc.check_verify(run)
            self.assertIn("独立", str(ctx.exception))

    def test_same_agent_as_reviewer_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = build_run(
                Path(tmp),
                author={"agent_id": "math-solver", "context_id": "ctx-1", "route": "导数定义法"},
                reviewer={"id": "math-solver", "role": "independent_agent",
                          "independent_from_solver": True, "context_id": "ctx-2"},
            )
            with self.assertRaises(mc.GateError) as ctx:
                mc.check_verify(run)
            self.assertIn("独立", str(ctx.exception))

    # --- D4: risk level could be downgraded by the solver to skip human sign-off ---
    def test_standard_risk_requires_written_rationale(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            run = build_run(base)
            problem = json.loads((run / "problem.json").read_text(encoding="utf-8"))
            problem["risk_rationale"] = ""
            (run / "problem.json").write_text(json.dumps(problem, ensure_ascii=False),
                                              encoding="utf-8")
            with self.assertRaises(mc.GateError) as ctx:
                mc.check_verify(run)
            self.assertIn("risk_rationale", str(ctx.exception))

    def test_proof_obligation_forces_high_risk_and_human_signoff(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = build_run(Path(tmp), proof_obligation=True)
            with self.assertRaises(mc.GateError) as ctx:
                mc.check_verify(run)
            self.assertIn("高风险", str(ctx.exception))

    # --- D6: malformed run.json produced a raw KeyError traceback ---
    def test_missing_run_json_field_is_a_gate_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = build_run(Path(tmp))
            (run / "run.json").write_text(json.dumps({"schema_version": "0.1.0"},
                                                     ensure_ascii=False), encoding="utf-8")
            with self.assertRaises(mc.GateError):
                mc.check_intake(run)

    # --- D5: a silent audio track satisfied the "voiced lesson" gate ---
    @unittest.skipUnless(HAVE_FFMPEG, "ffmpeg/ffprobe not installed")
    def test_silent_audio_track_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = extend_to_manim(build_run(Path(tmp)))
            make_mp4(run, silent=True)
            with self.assertRaises(mc.GateError) as ctx:
                mc.check_video(run)
            self.assertIn("静音", str(ctx.exception))

    @unittest.skipUnless(HAVE_FFMPEG, "ffmpeg/ffprobe not installed")
    def test_real_tone_audio_track_is_accepted(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = extend_to_manim(build_run(Path(tmp)))
            make_mp4(run, silent=False)
            _, length = mc.check_video(run)
            self.assertGreater(length, 1)

    # --- D8: scripts hard-crashed on Python < 3.11 with a bare ImportError ---
    def test_scripts_report_python_requirement_clearly(self):
        legacy = find_legacy_interpreter()
        if legacy is None:
            self.skipTest("no Python 3.9/3.10 interpreter available")
        result = subprocess.run(
            [legacy, str(ROOT / "scripts" / "sync_agents.py"), "--check"],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        self.assertIn("3.11", result.stderr)


class CodexConfigAccuracyTest(unittest.TestCase):
    """The Codex profile must only claim what codex actually reads."""

    def test_codex_config_only_uses_verified_keys(self):
        import tomllib
        data = tomllib.loads((ROOT / ".codex/config.toml").read_text(encoding="utf-8"))
        agents = data.get("agents", {})
        # Verified against codex 0.157.1 with --strict-config type probes.
        self.assertIn("enabled", agents)
        self.assertIsInstance(agents["enabled"], bool)
        self.assertIsInstance(agents["max_concurrent_threads_per_session"], int)

    def test_codex_role_files_match_real_role_schema(self):
        """codex_agent_roles::loader requires name + description + developer_instructions."""
        import tomllib
        files = sorted((ROOT / ".codex/agents").glob("*.toml"))
        self.assertEqual(len(files), 10)
        for path in files:
            role = tomllib.loads(path.read_text(encoding="utf-8"))
            for field in ("name", "description", "developer_instructions"):
                self.assertTrue(role.get(field), f"{path.name} missing {field}")
            self.assertEqual(role["name"], path.stem)


if __name__ == "__main__":
    unittest.main()
