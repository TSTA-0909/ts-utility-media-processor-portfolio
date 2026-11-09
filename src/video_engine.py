# -*- coding: utf-8 -*-
from __future__ import annotations

import os
import subprocess
from pathlib import Path

try:
    import imageio_ffmpeg
except ImportError:
    imageio_ffmpeg = None

VIDEO_EXTENSIONS = {".mp4", ".mov", ".m4v", ".avi", ".mkv", ".webm"}

VIDEO_PRESETS = {
    "家族動画向け（おすすめ）": {"crf": 23, "max_height": 1080, "audio_bitrate": "128k", "preset": "medium", "description": "見た目をなるべく保ちながら容量を減らします。4K動画は最大1080pへ縮小します。家族動画の長期保存向け。"},
    "高画質（画質優先）": {"crf": 20, "max_height": 1080, "audio_bitrate": "160k", "preset": "slow", "description": "画質を優先します。容量削減は控えめですが、元動画との差が出にくい設定です。"},
    "容量優先（かなり軽量）": {"crf": 28, "max_height": 720, "audio_bitrate": "96k", "preset": "medium", "description": "スマホ閲覧を中心に容量を大きく減らします。最大720pへ縮小します。"},
}
DEFAULT_VIDEO_PRESET = "家族動画向け（おすすめ）"


def get_ffmpeg_exe() -> str:
    """imageio-ffmpeg同梱FFmpegを優先して返す。"""
    if imageio_ffmpeg is not None:
        return imageio_ffmpeg.get_ffmpeg_exe()
    return "ffmpeg"


def build_output_path(source: Path, output_dir: Path) -> Path:
    destination = output_dir / f"{source.stem}_slim.mp4"
    if not destination.exists():
        return destination
    counter = 2
    while True:
        candidate = output_dir / f"{source.stem}_slim_{counter}.mp4"
        if not candidate.exists():
            return candidate
        counter += 1


def compress_video(source: Path, destination: Path, preset_name: str) -> None:
    if preset_name not in VIDEO_PRESETS:
        raise ValueError(f"不明な動画プリセットです: {preset_name}")
    preset = VIDEO_PRESETS[preset_name]
    destination.parent.mkdir(parents=True, exist_ok=True)
    ffmpeg_exe = get_ffmpeg_exe()
    max_height = int(preset["max_height"])
    vf = (f"scale='if(gt(ih,{max_height}),trunc(iw*{max_height}/ih/2)*2,trunc(iw/2)*2)':" f"'if(gt(ih,{max_height}),{max_height},trunc(ih/2)*2)'")
    cmd = [ffmpeg_exe, "-hide_banner", "-loglevel", "error", "-y", "-i", str(source), "-map", "0:v:0", "-map", "0:a?", "-map_metadata", "0", "-vf", vf, "-c:v", "libx264", "-preset", str(preset["preset"]), "-crf", str(preset["crf"]), "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", str(preset["audio_bitrate"]), "-movflags", "+faststart+use_metadata_tags", str(destination)]
    startupinfo = None
    creationflags = 0
    if os.name == "nt":
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        creationflags = subprocess.CREATE_NO_WINDOW
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, startupinfo=startupinfo, creationflags=creationflags)
    except FileNotFoundError as exc:
        exists = Path(ffmpeg_exe).exists() if ffmpeg_exe != "ffmpeg" else False
        raise RuntimeError(
            "FFmpeg実行ファイルを起動できませんでした。\n"
            f"FFmpegパス: {ffmpeg_exe}\n"
            f"パス上の存在確認: {'あり' if exists else 'なし'}\n"
            f"元エラー: {exc}"
        ) from exc
    if result.returncode != 0:
        raise RuntimeError(
            "FFmpegによる動画変換に失敗しました。\n"
            f"FFmpegパス: {ffmpeg_exe}\n"
            f"終了コード: {result.returncode}\n"
            f"詳細: {result.stderr.strip() or '詳細なし'}"
        )
