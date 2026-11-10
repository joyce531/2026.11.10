"""Prepare browser-compatible MP4 copies of Godot lesson videos; never edit source files."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

PROJECT = Path(__file__).resolve().parents[2]
WEB = PROJECT / "web"
GODOT = Path(r"D:\dachuang\naxi-game")
CONTENT = GODOT / "Data/content.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def probe(executable: Path, path: Path) -> dict:
    completed = subprocess.run(
        [str(executable), "-v", "error", "-show_entries",
         "format=duration,format_name:stream=codec_name,codec_type,width,height,sample_rate,channels",
         "-of", "json", str(path)], capture_output=True, text=True, check=True,
    )
    return json.loads(completed.stdout)


def video_audio(metadata: dict, video: str, audio: str) -> bool:
    codecs = {stream.get("codec_type"): stream.get("codec_name") for stream in metadata["streams"]}
    return codecs.get("video") == video and codecs.get("audio") == audio


def same_frames(original: Path, converted: Path, original_duration: float) -> bool:
    """Check the pre-existing step-03 MP4 is the same footage, not merely same filename."""
    import cv2
    import numpy as np

    first = cv2.VideoCapture(str(original))
    second = cv2.VideoCapture(str(converted))
    try:
        errors = []
        for fraction in (0.12, 0.5, 0.88):
            timestamp = fraction * original_duration * 1000
            first.set(cv2.CAP_PROP_POS_MSEC, timestamp)
            second.set(cv2.CAP_PROP_POS_MSEC, timestamp)
            valid_a, frame_a = first.read()
            valid_b, frame_b = second.read()
            if not valid_a or not valid_b:
                return False
            if frame_a.shape != frame_b.shape:
                return False
            errors.append(float(np.abs(frame_a.astype(np.float32) - frame_b.astype(np.float32)).mean()))
        print(f"Existing step-03 MP4 frame MAE: {[round(value, 2) for value in errors]}")
        return max(errors) < 28
    finally:
        first.release()
        second.release()


def entries(group: str, data: dict) -> list[tuple[str, Path, Path]]:
    if group == "music":
        paths = [question["prompt"]["audio"] for question in data["quizzes"]["music"]["questions"]]
        folder = PROJECT / "data/music/videos"
    else:
        dance = data["dances"]["datiao_01"]
        paths = [dance["full_video"], *[step["video"] for step in dance["steps"]]]
        folder = PROJECT / "data/dance/dance_videos"
    return [(path, folder / Path(path).name, GODOT / path.removeprefix("res://")) for path in paths]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("group", choices=("music", "dance"))
    parser.add_argument("--ffmpeg", type=Path, default=shutil.which("ffmpeg"))
    args = parser.parse_args()
    if not args.ffmpeg or not args.ffmpeg.is_file():
        raise SystemExit("FFmpeg 未找到；请传入已安装 ffmpeg.exe 的 --ffmpeg 路径")
    ffprobe = args.ffmpeg.with_name("ffprobe.exe")
    if not ffprobe.is_file():
        raise SystemExit("ffprobe.exe 未找到；不能验证输出")
    if not (GODOT / "project.godot").is_file():
        raise SystemExit("Godot 原工程不存在；停止处理")
    data = json.loads(CONTENT.read_text(encoding="utf-8"))
    manifest = []
    for game_path, source, original in entries(args.group, data):
        if not source.is_file() or not original.is_file() or sha256(source) != sha256(original):
            raise SystemExit(f"源视频缺失或与 Godot 引用不一致：{game_path}")
        source_meta = probe(ffprobe, source)
        if not video_audio(source_meta, "theora", "vorbis"):
            raise SystemExit(f"源视频编码与审计不符：{source}")
        source_duration = float(source_meta["format"]["duration"])
        destination = WEB / "public/game_media" / args.group / (source.stem + ".mp4")
        destination.parent.mkdir(parents=True, exist_ok=True)
        reused = False
        if args.group == "dance" and source.stem == "datiao_01_step_03":
            existing = list(source.parent.glob("datiao_01_step_03*.mp4"))
            if len(existing) == 1:
                existing_meta = probe(ffprobe, existing[0])
                if (video_audio(existing_meta, "h264", "aac")
                    and abs(float(existing_meta["format"]["duration"]) - source_duration) < 0.2
                    and same_frames(source, existing[0], source_duration)):
                    if not destination.exists():
                        shutil.copy2(existing[0], destination)
                    reused = True
        if not destination.exists():
            subprocess.run([
                str(args.ffmpeg), "-hide_banner", "-loglevel", "error", "-i", str(source),
                "-map", "0:v:0", "-map", "0:a:0", "-c:v", "libx264", "-preset", "veryfast",
                "-crf", "25", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k",
                "-movflags", "+faststart", "-n", str(destination),
            ], check=True)
        output_meta = probe(ffprobe, destination)
        if not video_audio(output_meta, "h264", "aac"):
            raise SystemExit(f"浏览器副本缺少 H.264 视频或 AAC 音轨：{destination}")
        if abs(float(output_meta["format"]["duration"]) - source_duration) > 0.3:
            raise SystemExit(f"副本时长与原视频差距过大：{destination}")
        # Decode a sample frame and audio segment, not merely the container header.
        subprocess.run([str(args.ffmpeg), "-v", "error", "-ss", "1", "-i", str(destination),
                        "-frames:v", "1", "-f", "null", "NUL"], check=True)
        subprocess.run([str(args.ffmpeg), "-v", "error", "-ss", "1", "-i", str(destination),
                        "-t", "1", "-vn", "-f", "null", "NUL"], check=True)
        manifest.append({
            "game_path": game_path,
            "source": source.relative_to(PROJECT).as_posix(),
            "source_sha256": sha256(source),
            "web_path": "/game_media/" + args.group + "/" + destination.name,
            "web_sha256": sha256(destination),
            "source_format": source_meta["format"]["format_name"],
            "source_duration_seconds": source_duration,
            "output_duration_seconds": float(output_meta["format"]["duration"]),
            "source_streams": source_meta["streams"],
            "output_streams": output_meta["streams"],
            "reused_existing_mp4": reused,
        })
        print(f"Prepared {destination.name} ({'existing MP4' if reused else 'new copy'})")
    manifest_path = WEB / "src/game" / f"{args.group}_video_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Verified {len(manifest)} {args.group} MP4 files with video and audio streams")


if __name__ == "__main__":
    main()
