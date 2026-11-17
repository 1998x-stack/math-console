#!/usr/bin/env python3
"""Generate an editable 16:9 teacher practice deck (students first, answers last)."""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches,Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

ROOT=Path(__file__).resolve().parents[4]
NAVY=RGBColor(23,40,63)
TEAL=RGBColor(20,143,139)
GREY=RGBColor(91,109,125)
WHITE=RGBColor(255,255,255)

def shape_text(slide,x,y,w,h,text,size=28,bold=False,color=NAVY):
    box=slide.shapes.add_textbox(Inches(x),Inches(y),Inches(w),Inches(h))
    tf=box.text_frame
    tf.clear();tf.word_wrap=True
    tf.margin_left=Inches(.08);tf.margin_right=Inches(.08)
    tf.margin_top=Inches(.04);tf.margin_bottom=Inches(.04)
    p=tf.paragraphs[0];p.text=text;p.alignment=PP_ALIGN.LEFT
    for run in p.runs:
        run.font.name="Microsoft YaHei"
        run.font.size=Pt(size)
        run.font.bold=bold
        run.font.color.rgb=color
    return box

def base_slide(prs,section,number):
    slide=prs.slides.add_slide(prs.slide_layouts[6])
    bar=slide.shapes.add_shape(MSO_SHAPE.RECTANGLE,Inches(0),Inches(0),Inches(13.333),Inches(.14))
    bar.fill.solid();bar.fill.fore_color.rgb=TEAL
    bar.line.fill.background()
    shape_text(slide,.8,.42,11,.5,section,16,color=GREY)
    shape_text(slide,12.1,.42,.5,.5,str(number),13,color=GREY)
    return slide

def create_deck(data):
    prs=Presentation()
    prs.slide_width=Inches(13.333);prs.slide_height=Inches(7.5)
    items=data["items"]
    slide=base_slide(prs,"数学课堂练习 · Math Console",1)
    shape_text(slide,.8,2.0,11.7,1.2,data["lesson_title"],36,True)
    shape_text(slide,.8,3.6,11.4,1.5,f"{len(items)} 道练习  |  基础 · 迁移 · 挑战",22,color=TEAL)
    labels={"foundation":"基础","transfer":"迁移","challenge":"挑战"}
    for idx,item in enumerate(items,1):
        slide=base_slide(prs,f"学生练习 · {labels[item['difficulty']]}",len(prs.slides)+1)
        shape_text(slide,.8,1.25,11.6,.75,f"练习 {idx}  {labels[item['difficulty']]}",29,True,color=TEAL)
        size=27 if len(item["question"])<130 else 22
        shape_text(slide,.8,2.35,11.65,3.5,item["question"],size)
        shape_text(slide,.8,6.45,10,.42,f"建议时间：{item.get('minutes',3)} 分钟  |  先独立作答",14,color=GREY)
    slide=base_slide(prs,"教师答案区",len(prs.slides)+1)
    shape_text(slide,.8,2.3,11.4,1.1,"以下为教师答案与解析",34,True,color=TEAL)
    shape_text(slide,.8,3.6,11.2,1.0,"课堂投影请勿提前展示此部分。",21,color=GREY)
    for idx,item in enumerate(items,1):
        slide=base_slide(prs,"教师答案",len(prs.slides)+1)
        shape_text(slide,.8,1.17,11.7,.75,f"练习 {idx} · {labels[item['difficulty']]} — 答案",27,True,color=TEAL)
        shape_text(slide,.8,2.05,11.4,1.2,"答案：" + item["answer"],24,True)
        analysis="解析：" + item["solution"]
        shape_text(slide,.8,3.35,11.4,2.5,analysis,21 if len(analysis)<200 else 17)
        shape_text(slide,.8,6.45,11.3,.5,"知识点："+" / ".join(item["knowledge_tags"]),14,color=GREY)
    return prs

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--run",required=True,type=Path)
    args=p.parse_args();run=args.run.resolve()
    source=run/"practice.json"
    if not source.is_file():
        p.error("缺少 practice.json")
    data=json.loads(source.read_text(encoding="utf-8"))
    try:
        from jsonschema import Draft202012Validator
        schema=json.loads((ROOT/"schemas/practice.schema.json").read_text(encoding="utf-8"))
        Draft202012Validator(schema).validate(data)
    except Exception as exc:
        p.error(f"练习 JSON 不符合 schema: {exc}")
    path=run/"practice.pptx"
    create_deck(data).save(str(path))
    print("[PPTX]",path,"可编辑文本框；尚不支持原生 OMML 数学公式")
if __name__=="__main__":
    main()
