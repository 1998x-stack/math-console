#!/usr/bin/env python3
"""G5 release audit: verify a published release.json, or generate it with --generate.

Hashing and gate logic live in scripts/math_console.py so this wrapper and the CLI
cannot drift apart. Nothing here can mark a run released by itself.
"""
import argparse
import subprocess
import sys
from pathlib import Path

p = argparse.ArgumentParser(description=__doc__)
p.add_argument("--run", required=True)
p.add_argument("--generate", action="store_true",
               help="Regenerate release.json (only possible when every gate really passes)")
args = p.parse_args()
root = Path(__file__).resolve().parents[4]
command = ["release"] if args.generate else ["check", "--stage", "release"]
raise SystemExit(subprocess.call(
    [sys.executable, str(root / "scripts" / "math_console.py"), *command, "--run", args.run]
))
