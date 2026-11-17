#!/usr/bin/env python3
"""Contract checks for every canonical skill and its versioned manifest."""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / ".agents" / "skills"
SEMVER = re.compile(r"^\d+\.\d+\.\d+$")
SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

def main():
    errors = []
    if not SKILLS.is_dir():
        errors.append(f"技能目录不存在: {SKILLS}")
    else:
        for directory in sorted(x for x in SKILLS.iterdir() if x.is_dir()):
            skill = directory / "SKILL.md"
            manifest = directory / "manifest.json"
            if not skill.is_file() or not manifest.is_file():
                errors.append(f"{directory.name}: 缺少 SKILL.md 或 manifest.json")
                continue
            body = skill.read_text(encoding="utf-8")
            if not body.startswith("---\n"):
                errors.append(f"{directory.name}: 缺少 YAML 前置元数据")
            else:
                front = body.split("---", 2)[1]
                if not re.search(rf"^name:\s*{re.escape(directory.name)}\s*$", front, re.M):
                    errors.append(f"{directory.name}: name 必须等于目录名")
                if not re.search(r"^description:\s*\S+", front, re.M):
                    errors.append(f"{directory.name}: 缺少可发现的 description")
            try:
                data = json.loads(manifest.read_text(encoding="utf-8"))
            except (OSError, ValueError) as exc:
                errors.append(f"{directory.name}: JSON 无效: {exc}")
                continue
            if data.get("id") != directory.name or not SLUG.fullmatch(directory.name):
                errors.append(f"{directory.name}: id 与目录或命名规则不一致")
            if not SEMVER.fullmatch(data.get("version", "")):
                errors.append(f"{directory.name}: 版本不是 semver")
            for group in ("references", "scripts", "assets"):
                entries = data.get(group, [])
                if not isinstance(entries, list) or not entries:
                    errors.append(f"{directory.name}: {group} 不能为空")
                else:
                    for relative in entries:
                        candidate = (directory / relative).resolve()
                        if not candidate.is_relative_to(directory.resolve()) or not candidate.is_file():
                            errors.append(f"{directory.name}: 缺少/越界资源 {relative}")
            link = ROOT / ".claude" / "skills" / directory.name
            if not link.is_symlink() or link.resolve() != directory.resolve():
                errors.append(f"{directory.name}: Claude 技能符号链接不存在或目标错误")
    if errors:
        print("\n".join(f"[FAIL] {error}" for error in errors))
        return 1
    print(f"[PASS] {len(list(SKILLS.iterdir()))} 个 Skills：元数据、资源路径、Claude 链接全部有效")
    return 0

if __name__ == "__main__":
    sys.exit(main())
