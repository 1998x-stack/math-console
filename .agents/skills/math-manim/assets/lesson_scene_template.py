"""Editable starter — replace with content mapped from storyboard.json.

Manim Community v0.19.x; render only inside sandbox.
"""
from math import log
from manim import *

class LessonScene(Scene):
    def construct(self):
        # beat_id: intro, step_ids: s1
        title = Text("导数的几何意义", font="Noto Sans CJK SC", font_size=38)
        formula = MathTex(r"f(x)=x\ln x-a x").scale(0.86)
        formula.next_to(title, DOWN, buff=0.45)
        self.play(Write(title))
        self.play(Write(formula))
        self.wait(2)

        # beat_id: derivative, step_ids: s2
        derivative = MathTex(r"f'(x)=\ln x+1-a").scale(0.95)
        derivative.move_to(formula.get_center())
        self.play(TransformMatchingTex(formula, derivative))
        self.wait(3)

        # Replace this template with the exact audited storyboard content.
        self.play(FadeOut(title), FadeOut(derivative))
