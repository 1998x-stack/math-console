#!/usr/bin/env python3
"""Regenerate a release report or verify its existing SHA-256 artifact inventory."""
import argparse,hashlib,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
p=argparse.ArgumentParser(description=__doc__)
p.add_argument("--run",required=True,type=Path)
p.add_argument("--generate",action="store_true")
args=p.parse_args()
run=args.run.resolve()
if args.generate:
    raise SystemExit(subprocess.call([sys.executable,str(ROOT/"scripts/math_console.py"),"release","--run",str(run)]))
report=run/"release.json"
if not report.is_file():
    p.error("release.json 不存在。请先通过全部阶段，再用 --generate")
data=json.loads(report.read_text(encoding="utf-8"))
for name,expected in data["artifacts"].items():
    file=(run/name).resolve()
    if not file.is_relative_to(run) or not file.is_file():
        p.error(f"文件缺失/非法路径: {name}")
    sha=hashlib.sha256(file.read_bytes()).hexdigest()
    if sha!=expected["sha256"] or file.stat().st_size!=expected["size_bytes"]:
        p.error(f"文件自发布后被修改: {name}")
print("[PASS] release.json 中的所有产物哈希一致")
