#!/usr/bin/env python3
"""Sample actual video frames for Agent-native visual QA. Never interpret pictures."""
from __future__ import annotations
import argparse
import hashlib
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def frame_plan(board: dict) -> list[dict]:
    seconds = 0.0
    frames = []
    for i, beat in enumerate(board["beats"], 1):
        duration = float(beat["duration_s"])
        if duration <= 0:
            raise ValueError("Non-positive beat duration")
        frames.append({
            "beat_id": beat["id"], "step_ids": beat["step_ids"],
            "time_s": round(seconds + duration / 2, 3),
            "frame": f"reviews/frame_{i:03d}.png",
            "verdict": "pending", "frame_sha256": None,
            "math_correct": None, "layout_ok": None, "narration_aligned": None,
            "notes": "",
        })
        seconds += duration
    return frames


def build_review(run: Path, *, extract: bool = True) -> dict:
    run = run.resolve()
    video = run / "lesson.mp4"
    boardfile = run / "storyboard.json"
    ppt = run / "practice.pptx"
    if not video.is_file() or not boardfile.is_file():
        raise ValueError("Missing real lesson.mp4 or storyboard.json")
    frames = frame_plan(json.loads(boardfile.read_text(encoding="utf-8")))
    if extract:
        if not shutil.which("ffmpeg"):
            raise RuntimeError("ffmpeg unavailable")
        directory = run / "reviews"
        if directory.is_symlink():
            raise ValueError("Unsafe reviews symlink")
        directory.mkdir(exist_ok=True)
        for item in frames:
            output = run / item["frame"]
            subprocess.run([
                "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                "-ss", str(item["time_s"]), "-i", str(video),
                "-frames:v", "1", str(output),
            ], check=True, timeout=90)
            if not output.is_file() or output.stat().st_size < 128:
                raise RuntimeError("Failed to extract actual frame: " + str(output))
            item["frame_sha256"] = digest(output)
    return {
        "schema_version": "0.1.0",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "method": "agent_native_vision",
        "status": "pending",
        "video_sha256": digest(video),
        "storyboard_sha256": digest(boardfile),
        "ppt_sha256": digest(ppt) if ppt.is_file() else None,
        "reviewer": {"agent_id": None, "context_id": None},
        "scenes": frames,
        "ppt_review": {"status": "pending", "notes": ""},
    }


def check_review(run: Path) -> dict:
    run = run.resolve()
    data = json.loads((run / "media-review.json").read_text(encoding="utf-8"))
    if data.get("method") != "agent_native_vision" or data.get("status") != "reviewed":
        raise ValueError("Review still pending or not agent-native")
    if digest(run / "lesson.mp4") != data.get("video_sha256"):
        raise ValueError("Video changed since review")
    if digest(run / "storyboard.json") != data.get("storyboard_sha256"):
        raise ValueError("Storyboard changed since review")
    if not data.get("ppt_sha256"):
        raise ValueError("PPT was not present when visual review was prepared")
    if digest(run / "practice.pptx") != data["ppt_sha256"]:
        raise ValueError("PPT changed since review")
    if not all(data.get("reviewer", {}).get(k) for k in ("agent_id", "context_id")):
        raise ValueError("Missing independent reviewer identity evidence")
    if not data.get("scenes"):
        raise ValueError("No scenes to review")
    for s in data["scenes"]:
        path = (run / s["frame"]).resolve()
        if not path.is_relative_to(run) or not path.is_file():
            raise ValueError("Missing/unsafe scene frame")
        if not s.get("frame_sha256") or digest(path) != s["frame_sha256"]:
            raise ValueError("Scene frame bytes changed since review")
        if (s["verdict"] != "pass" or s["math_correct"] is not True or
                s["layout_ok"] is not True or s["narration_aligned"] is not True or
                not s["notes"].strip()):
            raise ValueError("Unreviewed or failed scene: " + s["beat_id"])
    if data.get("ppt_review", {}).get("status") != "pass":
        raise ValueError("PPT visual review missing")
    return data


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--run", required=True, type=Path)
    modes = p.add_mutually_exclusive_group()
    modes.add_argument("--dry-run", action="store_true")
    modes.add_argument("--check", action="store_true")
    args = p.parse_args()
    try:
        if args.check:
            r = check_review(args.run)
            print("[PASS]", len(r["scenes"]), "scenes of agent visual evidence")
            return
        r = build_review(args.run, extract=not args.dry_run)
        if args.dry_run:
            print(json.dumps(r, ensure_ascii=False, indent=2))
            return
        path = args.run.resolve() / "media-review.json"
        if path.exists():
            raise ValueError("Refusing to overwrite existing media review")
        path.write_text(json.dumps(r, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print("[PENDING] Frames extracted. A real Agent must visually inspect each frame.")
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        p.exit(2, "[BLOCKED] " + str(error) + "\n")


if __name__ == "__main__":
    main()
