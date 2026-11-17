"""Deterministic fixture tests. No mathematical image content parsing is performed."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class QaToolsTest(unittest.TestCase):
    def test_storyboard_sample_midpoints(self):
        mod = load("scripts/prepare_media_review.py", "prepare_media_review")
        got = mod.frame_plan({"beats": [
            {"id": "b1", "duration_s": 10, "step_ids": ["s1"]},
            {"id": "b2", "duration_s": 12, "step_ids": ["s2"]},
        ]})
        self.assertEqual([x["time_s"] for x in got], [5.0, 16.0])
        self.assertTrue(all(x["verdict"] == "pending" for x in got))

    def test_nonpositive_beat_rejected(self):
        mod = load("scripts/prepare_media_review.py", "prepare_media_review_invalid")
        with self.assertRaises(ValueError):
            mod.frame_plan({"beats": [{"id": "x", "duration_s": 0, "step_ids": []}]})

    def test_missing_cost_remains_null(self):
        mod = load("scripts/summarize_agent_usage.py", "usage_summary")
        with tempfile.TemporaryDirectory() as d:
            source = Path(d) / "events.jsonl"
            source.write_text(json.dumps({"status": "complete", "stage": "solve",
                                          "input_tokens": 99, "output_tokens": 10,
                                          "duration_ms": 1200}), encoding="utf-8")
            got = mod.summarize(source)
            self.assertIsNone(got["total_cost_usd"])
            self.assertEqual(got["total_input_tokens"], 99)

    def test_partial_usage_never_guesses_total(self):
        mod = load("scripts/summarize_agent_usage.py", "usage_summary_partial")
        with tempfile.TemporaryDirectory() as d:
            source = Path(d) / "events.jsonl"
            source.write_text('{"stage":"solve","input_tokens":12,"output_tokens":3}\n'
                              '{"stage":"verify","status":"blocked"}\n', encoding="utf-8")
            got = mod.summarize(source)
            self.assertIsNone(got["total_input_tokens"])
            self.assertEqual(got["events"], 2)



    def test_scene_frame_and_ppt_hashes_must_match(self):
        mod = load("scripts/prepare_media_review.py", "prepare_media_review_hashes")
        with tempfile.TemporaryDirectory() as d:
            run = Path(d)
            (run / "lesson.mp4").write_bytes(b"v" * 2048)
            (run / "storyboard.json").write_text(json.dumps({"beats": [
                {"id": "b1", "step_ids": ["s1"], "duration_s": 3}
            ]}), encoding="utf-8")
            (run / "practice.pptx").write_bytes(b"p" * 2048)
            data = mod.build_review(run, extract=False)
            (run / "reviews").mkdir()
            frame = run / data["scenes"][0]["frame"]
            frame.write_bytes(b"frame-bytes" * 50)
            data["scenes"][0].update({"frame_sha256": mod.digest(frame),
                                      "verdict": "pass", "math_correct": True,
                                      "layout_ok": True, "narration_aligned": True,
                                      "notes": "独立检查过画面、数学步骤、真实旁白"})
            data["reviewer"] = {"agent_id": "reviewer", "context_id": "actual-ctx"}
            data["ppt_review"] = {"status": "pass", "notes": "逐页检查完成"}
            data["status"] = "reviewed"
            (run / "media-review.json").write_text(json.dumps(data), encoding="utf-8")
            self.assertEqual(mod.check_review(run)["status"], "reviewed")
            frame.write_bytes(b"tampered-frame" * 50)
            with self.assertRaisesRegex(ValueError, "frame bytes changed"):
                mod.check_review(run)


if __name__ == "__main__":
    unittest.main()

    def test_review_fails_without_real_agent_visual_inspection(self):
        mod = load("scripts/prepare_media_review.py", "prepare_media_review_pending")
        with tempfile.TemporaryDirectory() as d:
            run = Path(d)
            (run / "lesson.mp4").write_bytes(b"x" * 2048)
            (run / "storyboard.json").write_text(json.dumps({"beats": [
                {"id": "b1", "step_ids": ["s1"], "duration_s": 3}
            ]}), encoding="utf-8")
            data = mod.build_review(run, extract=False)
            (run / "media-review.json").write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "pending"):
                mod.check_review(run)
