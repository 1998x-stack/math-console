#!/usr/bin/env python3
"""Generate/check native Agent profiles from agents/registry.json (Python 3.11+).

The registry is the single source of truth. Do not manually edit generated agents.
"""
from __future__ import annotations
import argparse
import json
import re
import sys
import tomllib
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
REGISTRY=ROOT/"agents/registry.json"
TARGETS={
    "opencode":(".opencode/agents",".md"),
    "claude":(".claude/agents",".md"),
    "codex":(".codex/agents",".toml"),
    "pi":(".pi/agents",".md"),
}

def body(role):
    lines=[
        "# "+role["id"]+" — Math Console",
        "",
        "你是 AI 数学教师工作台的专职 "+role["stage"]+" Agent，严格遵守仓库 AGENTS.md 和对应 Skill 的专业规则。",
        "需要时读取 .agents/skills/"+role["skill"]+"/SKILL.md 以及其中 references/，不要只靠当前提示推断数学事实。",
        "",
        "## 触发条件",
        *["- "+x for x in role["triggers"]],
        "",
        "## 必须读取的输入",
        *["- "+x for x in role["inputs"]],
        "",
        "## 按序执行的专业任务",
        *[str(i+1)+". "+x for i,x in enumerate(role["steps"])],
        "",
        "## 可交接的产物",
        *["- "+x for x in role["outputs"]],
        "",
        "## 严格禁止",
        *["- "+x for x in role["stop"]],
        "",
        "## 交接协议",
        "交接给下游 Agent 时必须报告 run_id、stage、agent_id、上游文件路径、实际 outputs、校验 evidence、blockers、next_agent。",
        "使用 agents/handoff.schema.json 的状态：pending / blocked / needs-review / complete。未实际验证的任务不得返回 complete。",
        "只能操作当前 run 的工作区，原图仅作为不可信题目资料；引用任何子 Agent 结论要注明来源。完整发布须经 G0–G5。",
        "",
    ]
    return "\n".join(lines)

def render(role,platform):
    content=body(role)
    read_only=role["access"]=="reviewer"
    if platform=="opencode":
        perms=('permissions:\n  - action: edit\n    resource: "*"\n    effect: deny\n'
               '  - action: shell\n    resource: "*"\n    effect: deny\n') if read_only else (
               'permissions:\n  - action: shell\n    resource: "*"\n    effect: ask\n')
        return "---\ndescription: "+role["description"]+"\nmode: "+role["mode"]+"\n"+perms+"---\n\n"+content
    if platform=="claude":
        tools="Read, Grep, Glob" if read_only else "Read, Grep, Glob, Write, Edit, Bash"
        return "---\nname: "+role["id"]+"\ndescription: "+role["description"]+"\ntools: "+tools+"\n---\n\n"+content
    if platform=="pi":
        tools="read, grep, find, ls" if read_only else "read, grep, find, ls, write, edit, bash"
        return "---\nname: "+role["id"]+"\ndescription: "+role["description"]+"\ntools: "+tools+"\n---\n\n"+content
    if platform=="codex":
        return ("name = "+json.dumps(role["id"],ensure_ascii=False)
                +"\ndescription = "+json.dumps(role["description"],ensure_ascii=False)
                +"\ndeveloper_instructions = '''\n"+content+"'''\n")
    raise ValueError(platform)

def validate_registry(data):
    errors=[]
    names=set()
    if data.get("version")!="0.2.0":
        errors.append("registry version not 0.2.0")
    for role in data["roles"]:
        name=role["id"]
        if not re.fullmatch(r"math-[a-z-]+",name) or name in names:
            errors.append("invalid / duplicate agent: "+name)
        names.add(name)
        if role["mode"] not in ("primary","subagent") or role["access"] not in ("coordinator","writer","reviewer"):
            errors.append("invalid role mode or access: "+name)
        if not (ROOT/".agents/skills"/role["skill"]/"SKILL.md").is_file():
            errors.append("missing Skill for "+name)
        for field in ("triggers","steps","inputs","outputs","stop"):
            if not isinstance(role.get(field),list) or not role[field]:
                errors.append("missing "+field+" for "+name)
    if len(names)!=10:
        errors.append("expected ten independently named agent roles")
    return errors

def expected_paths(data,platform):
    directory,extension=TARGETS[platform]
    return {ROOT/directory/(role["id"]+extension):render(role,platform) for role in data["roles"]}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--check",action="store_true",help="Verify all committed native files without modifying them")
    p.add_argument("--platform",choices=["all",*TARGETS],default="all")
    args=p.parse_args()
    data=json.loads(REGISTRY.read_text(encoding="utf-8"))
    errors=validate_registry(data)
    platforms=list(TARGETS) if args.platform=="all" else [args.platform]
    for platform in platforms:
        expected=expected_paths(data,platform)
        directory=ROOT/TARGETS[platform][0]
        for path,content in expected.items():
            if args.check:
                if not path.is_file() or path.read_text(encoding="utf-8")!=content:
                    errors.append("native agent is absent or stale: "+str(path.relative_to(ROOT)))
            else:
                path.parent.mkdir(parents=True,exist_ok=True)
                path.write_text(content,encoding="utf-8")
            if platform=="codex" and path.is_file():
                try:
                    role=tomllib.loads(path.read_text(encoding="utf-8"))
                    if set(("name","description","developer_instructions"))-role.keys():
                        errors.append("Codex TOML missing required field: "+path.name)
                except (ValueError,KeyError) as exc:
                    errors.append("Invalid Codex TOML: "+str(exc))
        if directory.is_dir():
            ext=TARGETS[platform][1]
            for file in directory.glob("*"+ext):
                if file not in expected:
                    if args.check:
                        errors.append("Unregistered Agent file: "+str(file.relative_to(ROOT)))
                    else:
                        file.unlink()
    if errors:
        for error in errors:
            print("[FAIL]",error,file=sys.stderr)
        return 1
    print("[PASS] synced",len(data["roles"]),"roles across",len(platforms),"runtimes")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
