#!/usr/bin/env python3
"""Inspect an existing teaching run without changing any artifacts."""
import argparse
import subprocess
import sys
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument("--run",required=True);args=p.parse_args()
root=Path(__file__).resolve().parents[4]
raise SystemExit(subprocess.call([sys.executable,str(root/"scripts/math_console.py"),"status","--run",args.run]))
