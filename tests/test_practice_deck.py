"""Practice PPTX must keep student questions separate from teacher solutions."""
import importlib.util
import json
import sys
import unittest
from pathlib import Path
from jsonschema import Draft202012Validator

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/".agents/skills/math-practice-ppt/scripts/build_slides.py"
spec=importlib.util.spec_from_file_location("math_practice_deck", SCRIPT)
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class PracticeDeckTest(unittest.TestCase):
    def test_contract_requires_teaching_objective(self):
        schema=json.loads((ROOT/"schemas/practice.schema.json").read_text(encoding="utf-8"))
        data={"schema_version":"0.2.0","problem_id":"demo","lesson_title":"练习",
              "items":[{"id":str(i),"difficulty":level,"question":"题目","answer":"答案",
                        "solution":"解析","knowledge_tags":["导数"],"target_step_ids":["s1"]}
                       for i,level in enumerate(("foundation","transfer","challenge"),1)]}
        self.assertTrue(list(Draft202012Validator(schema).iter_errors(data)))
        for item in data["items"]:
            item["teaching_objective"]="能独立完成求导。"
        self.assertFalse(list(Draft202012Validator(schema).iter_errors(data)))

    def test_answer_pages_separate_and_editable(self):
        practice={
            "schema_version":"0.2.0","problem_id":"demo",
            "lesson_title":"导数入门","items":[
                {"id":"p1","difficulty":"foundation","question":"题目一：x² 求导","answer":"答案一：2x","solution":"幂函数法则","teaching_objective":"掌握平方求导","knowledge_tags":["求导"],"target_step_ids":["s1"]},
                {"id":"p2","difficulty":"transfer","question":"题目二：x³ 求导","answer":"答案二：3x²","solution":"幂函数法则","teaching_objective":"掌握立方求导","knowledge_tags":["求导"],"target_step_ids":["s1"]},
                {"id":"p3","difficulty":"challenge","question":"题目三：x⁴ 求导","answer":"答案三：4x³","solution":"幂函数法则","teaching_objective":"掌握四次方求导","knowledge_tags":["求导"],"target_step_ids":["s1"]}
            ]
        }
        deck=module.create_deck(practice)
        self.assertEqual(len(deck.slides),8)
        def text(slides):
            return "\n".join(shape.text for slide in slides for shape in slide.shapes if shape.has_text_frame)
        student=text([deck.slides[i] for i in range(1,4)])
        teacher=text([deck.slides[i] for i in range(5,len(deck.slides))])
        for item in practice["items"]:
            self.assertIn(item["question"],student)
            self.assertNotIn(item["answer"],student)
            self.assertIn(item["answer"],teacher)
        self.assertTrue(any(shape.has_text_frame for slide in deck.slides for shape in slide.shapes))
        self.assertIn("教学目标：掌握平方求导",teacher)

    def test_cjk_font_is_native_on_macos(self):
        if sys.platform != "darwin":
            self.skipTest("macOS font fallback regression")
        self.assertEqual(module.CJK_FONT,"PingFang SC")
        deck=module.create_deck({"schema_version":"0.2.0","problem_id":"demo",
            "lesson_title":"中文字体","items":[
                {"id":str(i),"difficulty":difficulty,"question":"中文题目",
                 "answer":"中文答案","solution":"中文解析","teaching_objective":"中文目标","knowledge_tags":["导数"],
                 "target_step_ids":["s1"]}
                for i,difficulty in enumerate(("foundation","transfer","challenge"),1)]})
        names={run.font.name for slide in deck.slides for shape in slide.shapes
               if shape.has_text_frame for para in shape.text_frame.paragraphs for run in para.runs}
        self.assertEqual(names,{"PingFang SC"})
        for slide in deck.slides:
            for shape in slide.shapes:
                if shape.has_text_frame:
                    for para in shape.text_frame.paragraphs:
                        for run in para.runs:
                            self.assertIn('a:ea typeface="PingFang SC"',run._r.xml)

if __name__=="__main__":
    unittest.main()
