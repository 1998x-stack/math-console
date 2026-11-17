"""No external models, no Docker and no network required for the contract smoke test."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import math_console as mc

class WorkbenchSmokeTest(unittest.TestCase):
    def test_contract_gates(self):
        from PIL import Image
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            img = base / "source.png"
            Image.new("RGB", (32, 32), (255, 255, 255)).save(img)
            run = base / "run"
            mc.do_init(img, run)
            data = {
                "schema_version": "0.1.0", "problem_id": "test-001",
                "source": {"image_paths": ["input/problem.png"], "language": "zh-CN"},
                "stem": {"text": "求 f(x)=x² 的导数", "latex": "f(x)=x^2"},
                "questions": [{"id": "q1", "text": "求导", "latex": "f'(x)"}],
                "ambiguities": [], "knowledge_tags": ["导数"], "risk_level": "standard"
            }
            (run / "problem.json").write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
            mc.check_intake(run)
            solution = {
                "schema_version": "0.1.0", "problem_id": "test-001",
                "assumptions": ["x 为实数"],
                "steps": [{"id": "s1", "question_id": "q1", "claim": "求导", "latex": "2x",
                           "reason": "幂函数求导法则", "depends_on": []}],
                "results": [{"question_id": "q1", "conclusion": "导数为 2x", "latex": "2x"}],
            }
            (run / "solution.json").write_text(json.dumps(solution, ensure_ascii=False), encoding="utf-8")
            (run / "solution.md").write_text("# 解题\n\n" + "使用幂函数求导法则。\n" * 12, encoding="utf-8")
            mc.check_solve(run)
            with self.assertRaises(mc.GateError):
                mc.check_verify(run)
            audit = {
                "schema_version": "0.1.0", "problem_id": "test-001",
                "verdict": "pass",
                "reviewer": {"id": "independent-001", "role": "independent_agent",
                             "independent_from_solver": True},
                "independent_method": "根据导数定义独立复核，结果与幂函数法则一致",
                "checks": [{"id": "c1", "passed": True, "evidence": "极限展开 (x+h)^2",
                            "step_ids": ["s1"]}], "tested_cases": [],
                "human_review": {"required": False, "approved": False}
            }
            (run / "audit.json").write_text(json.dumps(audit, ensure_ascii=False), encoding="utf-8")
            mc.check_verify(run)
            board = {
                "schema_version": "0.1.0", "problem_id": "test-001",
                "lesson_title": "导数入门",
                "learning_objectives": ["理解幂函数求导法则"],
                "beats": [{"id": "b1", "step_ids": ["s1"], "visual": "画出抛物线",
                           "voiceover": "观察切线斜率", "pedagogy": "从几何直觉到计算",
                           "duration_s": 9}]
            }
            (run / "storyboard.json").write_text(json.dumps(board, ensure_ascii=False), encoding="utf-8")
            (run / "storyboard.md").write_text("# 教学分镜\n\n" + "解释导数几何意义。\n" * 8, encoding="utf-8")
            mc.check_storyboard(run)
            with self.assertRaises(mc.GateError):
                mc.check_manim(run)

if __name__ == "__main__":
    unittest.main()
