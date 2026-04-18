from pathlib import Path

def analyze_video(inputs_dir: Path):
    """Placeholder video analysis: count mp4 files and return names."""
    videos = list(Path(inputs_dir).glob("*.mp4"))
    return {
        "count": len(videos),
        "files": [v.name for v in videos],
        "note": "placeholder video analysis",
    }
