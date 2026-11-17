#!/usr/bin/env python3
"""Isolated Manim rendering + real narration muxing, never run generated Python on host.

Two modes:
- narration mode (default): requires a real --voiceover, renders in Docker, then muxes
  lesson.mp4 and runs the G4b gate (video + real audio stream + sync + non-silent level).
- --preview-only: renders the scene in the same isolated container and copies the result
  to silent.mp4 WITHOUT any audio track and WITHOUT creating lesson.mp4. Use it to
  inspect frames while narration is still missing. A silent preview is never a lesson.
"""
from __future__ import annotations
import argparse,os,shutil,subprocess,sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[4]
IMAGE="math-console/manim-zh:0.1.0"
def run_checked(cmd,timeout=600):
    print("+", " ".join(str(x) for x in cmd),flush=True)
    subprocess.run(cmd,check=True,timeout=timeout)

def media_duration(path):
    p=subprocess.run(["ffprobe","-v","error","-show_entries","format=duration",
        "-of","default=noprint_wrappers=1:nokey=1",str(path)],
        check=True,capture_output=True,text=True,timeout=30)
    return float(p.stdout.strip())

def parse_args(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--run",required=True,type=Path)
    p.add_argument("--voiceover",type=Path,
                   help="Actual TTS/teacher WAV/MP3 audio; required unless --preview-only")
    p.add_argument("--quality",choices=["l","m","h"],default="l")
    p.add_argument("--build-image",action="store_true")
    p.add_argument("--preview-only",action="store_true",
                   help="Render an isolated silent.mp4 preview; never creates lesson.mp4")
    p.add_argument("--image",default=os.getenv("MANIM_DOCKER_IMAGE",IMAGE))
    args=p.parse_args(argv)
    if not args.preview_only and not args.voiceover:
        p.error("必须提供真实旁白 --voiceover，或显式使用 --preview-only 生成无声预览")
    if args.voiceover and args.voiceover.suffix.lower() not in {".wav",".mp3",".m4a"}:
        p.error("旁白格式必须为 WAV/MP3/M4A")
    return args

def render_in_sandbox(args, work, media):
    for tool in ("docker","ffmpeg","ffprobe"):
        if not shutil.which(tool):
            raise RuntimeError("缺少外部工具: "+tool)
    run_checked([sys.executable,str(ROOT/"scripts/math_console.py"),"check","--run",str(work),"--stage","manim"],60)
    if args.build_image:
        run_checked(["docker","build","-f",str(ROOT/".agents/skills/math-video/assets/Dockerfile"),
                     "-t",args.image,str(ROOT)],1200)
    uid=f"{os.getuid()}:{os.getgid()}" if hasattr(os,"getuid") else "1000:1000"
    run_checked(["docker","run","--rm","--network=none","--read-only",
        "--cpus=2","--memory=3g","--pids-limit=128","--cap-drop=ALL",
        "--security-opt=no-new-privileges","--tmpfs","/tmp:rw,nosuid,size=512m",
        "--user",uid,"-e","HOME=/tmp","-e","XDG_CACHE_HOME=/tmp/.cache",
        "-v",f"{work}:/input:ro","-v",f"{media}:/render:rw",args.image,
        "manim",f"-q{args.quality}","--media_dir","/render",
        "/input/lesson_scene.py","LessonScene"],900)
    matches=sorted(media.rglob("LessonScene.mp4"),key=lambda x:x.stat().st_mtime,reverse=True)
    if not matches:
        raise RuntimeError("Docker 已退出但未找到真实 Manim MP4")
    return matches[0]

def run_render(args):
    work=args.run.resolve()
    if not work.is_dir():
        raise RuntimeError("run 目录不存在: "+str(work))
    voice=args.voiceover.resolve() if args.voiceover else None
    if voice is not None and not voice.is_file():
        raise RuntimeError("真实旁白文件不存在: "+str(voice))
    media=work/"media";media.mkdir(exist_ok=True)
    rendered=render_in_sandbox(args, work, media)
    silent=work/"silent.mp4"
    shutil.copy2(rendered,silent)
    length=media_duration(silent)
    if not 1<length<7200:
        raise RuntimeError(f"渲染结果时长异常：{length:.2f}s")
    if args.preview_only:
        print(f"[PREVIEW] {silent} 时长 {length:.2f}s；该文件没有音轨，不能称为讲解 MP4。")
        print("尚未生成 lesson.mp4：缺少真实中文旁白音轨时 G4b 不会通过。")
        return silent
    audio_length=media_duration(voice)
    if abs(length-audio_length)>3:
        raise RuntimeError(f"音画时长差超过 3 秒：video={length:.2f}s voice={audio_length:.2f}s；请调整分镜/配音")
    output=work/"lesson.mp4"
    run_checked(["ffmpeg","-y","-v","error","-i",str(silent),"-i",str(voice),
                 "-map","0:v:0","-map","1:a:0","-c:v","copy","-c:a","aac",
                 "-af","apad","-shortest","-movflags","+faststart",str(output)],180)
    run_checked([sys.executable,str(ROOT/"scripts/math_console.py"),
                 "check","--run",str(work),"--stage","video"],60)
    print("最终有声 MP4:",output)
    return output

def main(argv=None):
    run_render(parse_args(argv))

if __name__=="__main__":
    try: main()
    except (OSError,ValueError,subprocess.SubprocessError,RuntimeError) as exc:
        print("[BLOCKED]",exc,file=sys.stderr)
        raise SystemExit(2) from None
