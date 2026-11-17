"""Practice PPTX must keep student questions separate from teacher solutions."""
import importlib.util
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/".agents/skills/math-practice-ppt/scripts/build_slides.py"
spec=importlib.util.spec_from_file_location("math_practice_deck", SCRIPT)
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class PracticeDeckTest(unittest.TestCase):
    def test_answer_pages_separate_and_editable(self):
        practice={
            "schema_version":"0.1.0","problem_id":"demo",
            "lesson_title":"导数入门","items":[
                {"id":"p1","difficulty":"foundation","question":"题目一：x² 求导","answer":"答案一：2x","solution":"幂函数法则","knowledge_tags":["求导"],"target_step_ids":["s1"]},
                {"id":"p2","difficulty":"transfer","question":"题目二：x³ 求导","answer":"答案二：3x²","solution":"幂函数法则","knowledge_tags":["求导"],"target_step_ids":["s1"]},
                {"id":"p3","difficulty":"challenge","question":"题目三：x⁴ 求导","answer":"答案三：4x³","solution":"幂函数法则","knowledge_tags":["求导"],"target_step_ids":["s1"]}
            ]
        }
        deck=module.create_deck(practice)
        self.assertEqual(len(deck.slides),8)
        def text(slides):
            return "\n".join(shape.text for slide in slides for shape in slide.shapes if shape.has_text_frame)
        student=text(deck.slides[1:4])
        teacher=text(deck.slides[5:])
        for item in practice["items"]:
            self.assertIn(item["question"],student)
            self.assertNotIn(item["answer"],student)
            self.assertIn(item["answer"],teacher)
        self.assertTrue(any(shape.has_text_frame for slide in deck.slides for shape in slide.shapes))

if __name__=="__main__":
    unittest.main()
