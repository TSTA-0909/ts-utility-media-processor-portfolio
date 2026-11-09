"""Execute the user-supplied Python engine on synthetic demonstration data.

Usage: python tools/run_sample.py
Never overwrites a user's file. Only writes into output_demo.
"""
from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from image_engine import resize_image  # genuine application code
from processing_presets import IMAGE_PRESETS


def main() -> None:
    original = ROOT / "docs" / "assets" / "before.jpg"
    if not original.exists():
        raise SystemExit("Demo input image is missing.")
    output_dir = ROOT / "output_demo"
    output_dir.mkdir(exist_ok=True)
    for key, label in (
        ("share", "社内提出・共有用（推奨・最軽量）"),
        ("email", "メール添付用（軽量）"),
        ("report", "社内報告書用（標準）"),
        ("screen", "画面確認用（高画質）"),
    ):
        width, height, quality, _ = IMAGE_PRESETS[label]
        destination = output_dir / f"after-{key}.jpg"
        resize_image(original, destination, width, height, quality, "standard")
        saved = (1 - destination.stat().st_size / original.stat().st_size) * 100
        print(f"{label}: {original.stat().st_size:,} -> {destination.stat().st_size:,} bytes / reduction {saved:.1f}%")
    print("Saved outputs:", output_dir.resolve())


if __name__ == "__main__":
    main()
