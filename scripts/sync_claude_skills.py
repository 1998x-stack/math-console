#!/usr/bin/env python3
"""Replace tracked symlinks with local copies in a disposable worktree only.

WARNING: Replacing Git-tracked symlinks dirties the worktree. Never commit these copies.
"""
import argparse
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
p = argparse.ArgumentParser(description=__doc__)
p.add_argument("--copy", action="store_true", help="Copy skills for Windows environments lacking symlinks")
p.add_argument("--confirm-dirty-worktree", action="store_true", help="Acknowledge Git worktree changes")
args = p.parse_args()
if not args.copy or not args.confirm_dirty_worktree:
    p.error("必须同时传 --copy --confirm-dirty-worktree；仅在独立工作树使用")
target = ROOT / ".claude" / "skills"
target.mkdir(parents=True, exist_ok=True)
for item in (ROOT / ".agents" / "skills").iterdir():
    if not item.is_dir():
        continue
    dst = target / item.name
    if dst.is_symlink():
        dst.unlink()
    elif dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(item, dst)
    print("copied", item.name)
