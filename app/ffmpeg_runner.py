# app/ffmpeg_runner.py
import subprocess, json
from pathlib import Path
from typing import List, Dict

def transcode(video_path: Path, out_dir: Path, renditions: List[Dict]) -> List[Dict]:
    """
    renditions: list like [{"width":1920,"height":1080,"crf":18,"suffix":"1080p"}]
    Returns: list of {"path": str, "cmd": str}
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    outputs = []

    for r in renditions:
        w, h = r.get("width", 1280), r.get("height", -2)
        crf = r.get("crf", 23)
        suffix = r.get("suffix", f"{w}x{h}")
        out_file = out_dir / f"{video_path.stem}_{suffix}.mp4"

        cmd = [
            "ffmpeg", "-y",
            "-i", str(video_path),
            "-vf", f"scale={w}:{h}",
            "-c:v", "libx264",
            "-preset", "veryslow",     # <- pushes CPU harder
            "-crf", str(crf),
            "-c:a", "aac",
            str(out_file)
        ]
        # Run synchronously; if any fails, raise CalledProcessError
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        outputs.append({"path": str(out_file), "cmd": " ".join(cmd)})

    return outputs
