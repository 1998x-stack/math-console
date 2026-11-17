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


if __name__ == "__main__":
    unittest.main()
