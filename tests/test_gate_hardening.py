"""Negative tests for release-gate holes that let an unverifiable package ship.

Every test here was written after reproducing a concrete abuse case against the
gate. Structural validation still cannot prove mathematical truth; these tests
only stop the gate from *accepting evidence it never checked*.

Reproduced holes (see workspaces/<run>/reports/ for the raw probe logs):
- G4c-1  a PPTX that prints every answer on the student pages passed check_ppt.
- G4c-2  three identical foundation items passed although G4c requires
         foundation / transfer / challenge layers.
- G4b-1  a storyboard declaring 600 s next to a real 3 s MP4 passed check_video.
- G5-1   after release.json was written, mutating a released artifact changed
         nothing: `check --stage all` still printed PASS, and the CLI had no way
         to re-verify a published release.
- G4b-2  render_docker.py could not produce the documented silent.mp4 preview at
         all without a narration file, so the only reachable "preview" path was
         to fake a voiceover.
"""
import contextlib
import importlib.util
import io
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tests"))

import math_console as mc  # noqa: E402
from test_gate_integrity import (  # noqa: E402  (shared fixtures, same harness)
    HAVE_FFMPEG, build_run, extend_to_manim, make_mp4,
)

DIFFICULTIES = ("foundation", "transfer", "challenge")


def deck_module():
    spec = importlib.util.spec_from_file_location(
        "math_practice_deck_hardening",
        ROOT / ".agents/skills/math-practice-ppt/scripts/build_slides.py",
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def practice_data(difficulties=DIFFICULTIES, problem_id="t-1"):
    return {
        "schema_version": "0.2.0", "problem_id": problem_id, "lesson_title": "导数入门",
        "items": [
            {"id": f"p{i}", "difficulty": difficulty, "question": f"第{i}题：求 x^{i} 的导数",
             "answer": f"第{i}题答案：{i}x^{i-1}", "solution": "使用幂函数求导法则逐步计算。",
             "teaching_objective": "能用幂函数求导法则完成计算。",
             "knowledge_tags": ["求导"], "target_step_ids": ["s1"], "minutes": 3}
            for i, difficulty in enumerate(difficulties, start=1)
        ],
    }


def write_deck(run, data, *, module=None, save=None):
    (run / "practice.json").write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    module = module or deck_module()
    deck = save if save is not None else module.create_deck(data)
    deck.save(str(run / "practice.pptx"))
    return deck


def build_publishable(base: Path) -> Path:
    """A run that is complete up to and including a real voiced MP4."""
    run = extend_to_manim(build_run(base))
    # keep the storyboard brief so the declared duration matches the 3 s fixture clip
    board = json.loads((run / "storyboard.json").read_text(encoding="utf-8"))
    board["beats"][0]["duration_s"] = 3
    (run / "storyboard.json").write_text(json.dumps(board, ensure_ascii=False), encoding="utf-8")
    make_mp4(run, silent=False)
    return run


class PracticeDeckGateTest(unittest.TestCase):
    """G4c: student pages must not leak answers; all three layers must exist."""

    def test_answers_on_student_pages_are_rejected(self):
        from pptx import Presentation
        from pptx.util import Inches
        with tempfile.TemporaryDirectory() as tmp:
            run = extend_to_manim(build_run(Path(tmp)))
            data = practice_data()
            (run / "practice.json").write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
            prs = Presentation()
            prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
            leak = "\n".join(f"练习 {i} {item['question']}  答案：{item['answer']}"
                             for i, item in enumerate(data["items"], 1))
            first = prs.slides.add_slide(prs.slide_layouts[6])
            first.shapes.add_textbox(Inches(.8), .8, Inches(11), Inches(4)).text_frame.text = leak
            for _ in range(6):
                filler = prs.slides.add_slide(prs.slide_layouts[6])
                filler.shapes.add_textbox(Inches(.8), .8, Inches(11), Inches(1)).text_frame.text = "占位"
            prs.save(str(run / "practice.pptx"))
            with self.assertRaises(mc.GateError) as ctx:
                mc.check_practice(run)
            self.assertIn("学生页", str(ctx.exception))

    def test_answers_missing_from_teacher_pages_are_rejected(self):
        from pptx import Presentation
        from pptx.util import Inches
        with tempfile.TemporaryDirectory() as tmp:
            run = extend_to_manim(build_run(Path(tmp)))
            data = practice_data()
            (run / "practice.json").write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
            # student pages only: the declared answer section never appears
            prs = Presentation()
            prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
            for item in data["items"]:
                slide = prs.slides.add_slide(prs.slide_layouts[6])
                slide.shapes.add_textbox(Inches(.8), .4, Inches(11), Inches(.5)).text_frame.text = "学生练习 · 基础"
                slide.shapes.add_textbox(Inches(.8), 2.0, Inches(11), Inches(3)).text_frame.text = item["question"]
            for _ in range(4):
                filler = prs.slides.add_slide(prs.slide_layouts[6])
                filler.shapes.add_textbox(Inches(.8), .8, Inches(11), Inches(1)).text_frame.text = "占位页"
            prs.save(str(run / "practice.pptx"))
            with self.assertRaises(mc.GateError) as ctx:
                mc.check_practice(run)
            self.assertIn("教师答案页", str(ctx.exception))

    def test_single_layer_practice_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = extend_to_manim(build_run(Path(tmp)))
            write_deck(run, practice_data(("foundation", "foundation", "foundation")))
            with self.assertRaises(mc.GateError) as ctx:
                mc.check_practice(run)
            self.assertIn("迁移", str(ctx.exception))

    def test_three_layer_deck_passes_the_draft_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = extend_to_manim(build_run(Path(tmp)))
            write_deck(run, practice_data())
            mc.check_practice(run)  # no video needed: this is the "ready" level

    def test_practice_gate_still_blocks_the_publish_step_without_video(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = extend_to_manim(build_run(Path(tmp)))
            write_deck(run, practice_data())
            with self.assertRaises(mc.GateError):
                mc.check_ppt(run)  # publishable level still needs the voiced MP4

    def test_ppt_referencing_unknown_steps_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = extend_to_manim(build_run(Path(tmp)))
            data = practice_data()
            data["items"][0]["target_step_ids"] = ["s-does-not-exist"]
            write_deck(run, data)
            with self.assertRaises(mc.GateError) as ctx:
                mc.check_practice(run)
            self.assertIn("不存在", str(ctx.exception))


@unittest.skipUnless(HAVE_FFMPEG, "ffmpeg/ffprobe not installed")
class VideoConsistencyGateTest(unittest.TestCase):
    """G4b: a 3 second clip must not be shipped as a lesson the storyboard calls 10 minutes."""

    def test_video_shorter_than_declared_storyboard_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = build_publishable(Path(tmp))
            board = json.loads((run / "storyboard.json").read_text(encoding="utf-8"))
            board["beats"][0]["duration_s"] = 600
            (run / "storyboard.json").write_text(json.dumps(board, ensure_ascii=False), encoding="utf-8")
            with self.assertRaises(mc.GateError) as ctx:
                mc.check_video(run)
            self.assertIn("分镜", str(ctx.exception))

    def test_matching_storyboard_duration_still_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = build_publishable(Path(tmp))
            _, length = mc.check_video(run)
            self.assertGreater(length, 1)


class ReleaseFreshnessGateTest(unittest.TestCase):
    """G5: a published release must be re-verifiable and must not silently rot."""

    @staticmethod
    def _release_run(base: Path) -> Path:
        run = build_publishable(base)
        write_deck(run, practice_data())
        mc.do_release(run)
        return run

    @unittest.skipUnless(HAVE_FFMPEG, "ffmpeg/ffprobe not installed")
    def test_tampered_artifact_invalidates_the_release(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = self._release_run(Path(tmp))
            mc.check_release(run)
            (run / "solution.md").write_text("# 解题\n\n发布后被修改\n" * 20, encoding="utf-8")
            with self.assertRaises(mc.GateError) as ctx:
                mc.check_release(run)
            self.assertIn("发布后被修改", str(ctx.exception))

    @unittest.skipUnless(HAVE_FFMPEG, "ffmpeg/ffprobe not installed")
    def test_missing_release_report_is_a_clear_gate_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = build_publishable(Path(tmp))
            write_deck(run, practice_data())
            with self.assertRaises(mc.GateError) as ctx:
                mc.check_release(run)
            self.assertIn("release.json", str(ctx.exception))

    @unittest.skipUnless(HAVE_FFMPEG, "ffmpeg/ffprobe not installed")
    def test_release_records_reproducible_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = build_publishable(Path(tmp))
            write_deck(run, practice_data())
            report = mc.do_release(run)
            self.assertEqual(set(mc.STAGES) | {"practice"}, set(report["gate_status"]))
            self.assertTrue(all(v == "pass" for v in report["gate_status"].values()))
            # every released artifact is hashed, and the evidence is reproducible
            for name in mc.RELEASE_FILES:
                self.assertIn(name, report["artifacts"])
                self.assertEqual(len(report["artifacts"][name]["sha256"]), 64)
            toolchain = report["toolchain"]
            self.assertTrue(toolchain["python"].startswith("3."))
            self.assertIn("ffprobe", toolchain)
            evidence = report["gate_evidence"]
            self.assertIn("video", evidence)
            self.assertIn("audio_peak_dbfs", evidence["video"])
            self.assertLessEqual(evidence["video"]["audio_peak_dbfs"], 0.0)
            self.assertEqual(evidence["verify"]["independent_reviewer_context"],
                             "ctx-auditor-1")

    @unittest.skipUnless(HAVE_FFMPEG, "ffmpeg/ffprobe not installed")
    def test_teacher_package_approval_is_hashed_and_bound_to_artifacts(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = build_publishable(Path(tmp))
            write_deck(run, practice_data())
            approval = {
                "run_id": run.name,
                "approved": True,
                "reviewer_name": "测试教师",
                "approval_type": "user_self_attestation",
                "approved_artifact_sha256": {
                    name: mc.digest(run / name) for name in mc.RELEASE_FILES
                },
            }
            (run / mc.TEACHER_APPROVAL_FILE).write_text(
                json.dumps(approval, ensure_ascii=False), encoding="utf-8")
            report = mc.do_release(run)
            self.assertIn(mc.TEACHER_APPROVAL_FILE, report["artifacts"])
            mc.check_release(run)
            approval["approved_artifact_sha256"]["practice.json"] = "0" * 64
            (run / mc.TEACHER_APPROVAL_FILE).write_text(
                json.dumps(approval, ensure_ascii=False), encoding="utf-8")
            with self.assertRaises(mc.GateError) as ctx:
                mc.check_release(run)
            self.assertIn("教师批准证据所指产物已变更", str(ctx.exception))

    @unittest.skipUnless(HAVE_FFMPEG, "ffmpeg/ffprobe not installed")
    def test_release_requires_every_release_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = build_publishable(Path(tmp))
            write_deck(run, practice_data())
            report = mc.do_release(run)
            report["artifacts"].pop("storyboard.md")
            (run / "release.json").write_text(json.dumps(report, ensure_ascii=False),
                                              encoding="utf-8")
            with self.assertRaises(mc.GateError) as ctx:
                mc.check_release(run)
            self.assertIn("storyboard.md", str(ctx.exception))

    @unittest.skipUnless(HAVE_FFMPEG, "ffmpeg/ffprobe not installed")
    def test_cli_exposes_practice_and_release_stages(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = self._release_run(Path(tmp))
            ok = subprocess.run(
                [sys.executable, str(ROOT / "scripts/math_console.py"), "check",
                 "--run", str(run), "--stage", "release"],
                capture_output=True, text=True)
            self.assertEqual(ok.returncode, 0, ok.stderr)
            self.assertIn("[PASS] release", ok.stdout)
            (run / "solution.md").write_text("# 解题\n\n发布后被替换\n" * 20, encoding="utf-8")
            stale = subprocess.run(
                [sys.executable, str(ROOT / "scripts/math_console.py"), "check",
                 "--run", str(run), "--stage", "release"],
                capture_output=True, text=True)
            self.assertEqual(stale.returncode, 2)
            self.assertIn("发布后被修改", stale.stderr)

    @unittest.skipUnless(HAVE_FFMPEG, "ffmpeg/ffprobe not installed")
    def test_stage_all_notices_a_stale_release_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = self._release_run(Path(tmp))
            fresh = subprocess.run(
                [sys.executable, str(ROOT / "scripts/math_console.py"), "check",
                 "--run", str(run), "--stage", "all"], capture_output=True, text=True)
            self.assertEqual(fresh.returncode, 0, fresh.stderr)
            (run / "storyboard.md").write_text("# 教学分镜\n\n发布后被替换\n" * 20, encoding="utf-8")
            stale = subprocess.run(
                [sys.executable, str(ROOT / "scripts/math_console.py"), "check",
                 "--run", str(run), "--stage", "all"], capture_output=True, text=True)
            self.assertEqual(stale.returncode, 2)
            self.assertIn("发布后被修改", stale.stderr)

    @unittest.skipUnless(HAVE_FFMPEG, "ffmpeg/ffprobe not installed")
    def test_status_reports_draft_and_release_separately(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = build_publishable(Path(tmp))
            write_deck(run, practice_data())
            out = subprocess.run(
                [sys.executable, str(ROOT / "scripts/math_console.py"), "status", "--run", str(run)],
                capture_output=True, text=True, check=True).stdout
            self.assertIn("[PASS] practice", out)
            self.assertIn("[BLOCKED] release", out)


class ReleaseSkillScriptTest(unittest.TestCase):
    """The skill wrapper must delegate to the CLI instead of re-implementing hashing."""

    def test_skill_script_delegates_to_the_cli(self):
        text = (ROOT / ".agents/skills/math-release-qa/scripts/check_release.py").read_text(encoding="utf-8")
        self.assertIn("math_console.py", text)
        self.assertIn("--stage", text)
        self.assertIn("release", text)


class PreviewRenderModeTest(unittest.TestCase):
    """G4b-2: the silent preview must be reachable without inventing a voiceover."""

    @staticmethod
    def _module():
        spec = importlib.util.spec_from_file_location(
            "math_video_render_docker",
            ROOT / ".agents/skills/math-video/scripts/render_docker.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_preview_only_mode_never_mints_a_lesson_mp4(self):
        module = self._module()
        self.assertTrue(hasattr(module, "run_render"), "render logic must be importable for testing")
        with tempfile.TemporaryDirectory() as tmp:
            run = extend_to_manim(build_run(Path(tmp)))
            media = run / "media"
            media.mkdir()
            (media / "LessonScene.mp4").write_bytes(b"\x00" * 4096)
            calls = []
            module.run_checked = lambda cmd, timeout=600: calls.append([str(x) for x in cmd])
            module.media_duration = lambda path: 3.0
            args = module.parse_args(["--run", str(run), "--preview-only"])
            with mock.patch.object(module.shutil, "which", return_value="/usr/bin/mock"):
                module.run_render(args)
            self.assertTrue((run / "silent.mp4").is_file(), "preview must produce silent.mp4")
            self.assertFalse((run / "lesson.mp4").exists(), "preview must not mint lesson.mp4")
            self.assertTrue(any("docker" in c[0] for c in calls), "render must go through the sandbox")
            self.assertFalse(any("ffmpeg" == Path(c[0]).name for c in calls),
                             "preview mode must not mux an audio track")

    def test_narration_mode_still_requires_a_real_voiceover(self):
        module = self._module()
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                module.parse_args(["--run", "workspaces/pi-local-001"])


class ManifestIndexTest(unittest.TestCase):
    """The published stage index must not drift from the registry or the skill dirs."""

    @staticmethod
    def _module():
        spec = importlib.util.spec_from_file_location(
            "validate_skill_manifests", ROOT / "scripts" / "validate_skill_manifests.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_live_index_is_consistent(self):
        self.assertEqual([], self._module().check_project_index())

    def test_registry_version_drift_is_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            sandbox = Path(tmp)
            shutil.copytree(ROOT / ".agents", sandbox / ".agents")
            shutil.copytree(ROOT / "agents", sandbox / "agents")
            module = self._module()
            module.ROOT = sandbox
            module.SKILLS = sandbox / ".agents" / "skills"
            index_file = sandbox / ".agents" / "manifest.json"
            index = json.loads(index_file.read_text(encoding="utf-8"))
            index["registry_version"] = "0.0.1"
            index["stages"][1]["manifest"] = ".agents/skills/math-image-intake/SKILL.md"
            index_file.write_text(json.dumps(index, ensure_ascii=False), encoding="utf-8")
            errors = module.check_project_index()
            self.assertTrue(any("registry_version" in error for error in errors), errors)
            self.assertTrue(any("manifest 路径" in error for error in errors), errors)


if __name__ == "__main__":
    unittest.main()

class TeacherReviewPolicyTest(unittest.TestCase):
    """A default review waiver must never be reported as a real signed approval."""

    def test_default_waiver_allows_high_risk_with_independent_math_audit(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = build_run(Path(tmp), risk_level="high")
            path = run / "audit.json"
            audit = json.loads(path.read_text(encoding="utf-8"))
            audit["human_review"] = {"required": True, "approved": False}
            path.write_text(json.dumps(audit, ensure_ascii=False), encoding="utf-8")
            mc.check_verify(run)
            result = mc.teacher_review_decision(run, audit)
            self.assertEqual("waived_by_default_policy", result["decision"])
            self.assertFalse(result["real_teacher_signature_verified"])
            self.assertFalse(audit["human_review"]["approved"])

    def test_strict_requires_real_signoff(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = build_run(Path(tmp), risk_level="high")
            path = run / "run.json"
            data = json.loads(path.read_text(encoding="utf-8"))
            data["teacher_review_policy"] = "strict"
            path.write_text(json.dumps(data), encoding="utf-8")
            path = run / "audit.json"
            data = json.loads(path.read_text(encoding="utf-8"))
            data["human_review"] = {"required": True, "approved": False}
            path.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaises(mc.GateError) as error:
                mc.check_verify(run)
            self.assertIn("strict", str(error.exception))

    def test_waiver_does_not_bypass_independent_audit(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = build_run(Path(tmp), risk_level="high")
            path = run / "audit.json"
            data = json.loads(path.read_text(encoding="utf-8"))
            data["reviewer"]["context_id"] = "ctx-solver-1"
            data["human_review"] = {"required": True, "approved": False}
            path.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaises(mc.GateError):
                mc.check_verify(run)

    def test_invalid_review_policy_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = build_run(Path(tmp))
            path = run / "run.json"
            data = json.loads(path.read_text(encoding="utf-8"))
            data["teacher_review_policy"] = "pretend_approved"
            path.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaises(mc.GateError):
                mc.check_verify(run)
