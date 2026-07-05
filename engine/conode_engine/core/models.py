"""모델 다운로더 (M1) — PLAN §7: 모델 가중치는 앱에 미포함, 다운로더 제공.

models/ (gitignore) 에 캐시. 다운로드 실패 시 None 을 반환하고 노드는 폴백한다.
"""
from __future__ import annotations

import urllib.request
from pathlib import Path
from typing import Optional

MODELS_DIR = Path(__file__).resolve().parents[2] / "models"

REGISTRY = {
    "pose_landmarker_lite.task": (
        "https://storage.googleapis.com/mediapipe-models/pose_landmarker/"
        "pose_landmarker_lite/float16/latest/pose_landmarker_lite.task"
    ),
    "selfie_segmenter.tflite": (
        "https://storage.googleapis.com/mediapipe-models/image_segmenter/"
        "selfie_segmenter/float16/latest/selfie_segmenter.tflite"
    ),
}


def ensure_model(name: str, timeout: float = 60.0) -> Optional[Path]:
    url = REGISTRY.get(name)
    if url is None:
        return None
    dest = MODELS_DIR / name
    if dest.exists() and dest.stat().st_size > 0:
        return dest
    try:
        MODELS_DIR.mkdir(parents=True, exist_ok=True)
        tmp = dest.with_suffix(dest.suffix + ".part")
        with urllib.request.urlopen(url, timeout=timeout) as resp, open(tmp, "wb") as f:
            f.write(resp.read())
        tmp.replace(dest)
        return dest
    except Exception:
        return None
