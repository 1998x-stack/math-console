#!/usr/bin/env python3
"""Static scene checks; NOT a security boundary. Render in Docker only."""
import argparse,subprocess,sys
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument("--run",required=True);args=p.parse_args()
root=Path(__file__).resolve().parents[4]
raise SystemExit(subprocess.call([sys.executable,str(root/"scripts/math_console.py"),"check","--run",args.run,"--stage","manim"]))
