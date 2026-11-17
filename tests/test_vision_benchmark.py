"""Static metadata checks only; NEVER interpret benchmark images in Python."""
import json
import unittest
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "benchmarks" / "vision"

class VisionBenchmarkFixtureTest(unittest.TestCase):
    def test_original_case_assets_and_expected_answers(self):
        data = json.loads((BASE / "golden.json").read_text(encoding="utf-8"))
        self.assertEqual(data["policy"], "agent_native_vision_only")
        self.assertGreaterEqual(len(data["cases"]), 3)
        self.assertEqual({x["category"] for x in data["cases"]},
                         {"function_derivative", "analytic_geometry", "solid_geometry"})
        for case in data["cases"]:
            svg = BASE / case["file"]
            self.assertTrue(svg.is_file())
            root = ET.parse(svg).getroot()  # XML validity only, NOT image understanding
            self.assertTrue(root.tag.endswith("svg"))
            self.assertEqual(len(case["expected"]), case["question_count"])
            self.assertEqual(case["review_status"], "pending_real_agent_run")

if __name__ == "__main__":
    unittest.main()
