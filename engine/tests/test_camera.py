"""Camera 노드 테스트 (T6/T8) — 인코딩 경로를 실카메라 없이 결정적으로 검증.

버퍼에 합성 프레임을 직접 넣어 process() 가 numpy 프레임을 내는지, 프리뷰 인코더가
base64 JPEG 를 내는지 확인한다. 캡처 스레드/실디바이스는 기동하지 않는다.
"""
from __future__ import annotations

import base64

import numpy as np

from conode_engine.core.preview import encode_jpeg
from conode_engine.core.processor import FrameCtx
from conode_engine.nodes.camera import Camera


def _frame(h=180, w=320):
    return np.random.default_rng(0).integers(0, 255, (h, w, 3), dtype=np.uint8)


def test_process_returns_none_when_empty():
    cam = Camera("cam1")
    assert cam.process(FrameCtx(seq=0), {}) is None


def test_process_returns_numpy_frame():
    cam = Camera("cam1")
    cam.source.buf.put(_frame())
    out = cam.process(FrameCtx(seq=0), {})
    assert isinstance(out, np.ndarray)
    assert out.shape == (180, 320, 3)


def test_preview_encoder_makes_jpeg():
    cam = Camera("cam1")
    cam.source.buf.put(_frame())
    out = cam.process(FrameCtx(seq=0), {})
    b64 = encode_jpeg(out)
    assert isinstance(b64, str)
    assert base64.b64decode(b64)[:2] == b"\xff\xd8"  # JPEG SOI


def test_exposure_and_mirror_paths():
    cam = Camera("cam1")
    cam.set("exposure", 0.9)
    cam.set("mirror", True)
    cam.source.buf.put(_frame())
    out = cam.process(FrameCtx(seq=1), {})
    assert isinstance(out, np.ndarray) and out.shape == (180, 320, 3)


def test_camera_params_include_modulatable_exposure():
    cam = Camera("cam1")
    assert "exposure" in cam.modulation_targets()
