"""제스처 테스트 (M3, T21-T24) — one-euro · 규칙 · 노드 · 프레임→영역 디퓨전 통합."""
from __future__ import annotations

import numpy as np

from conode_engine.core.processor import FrameCtx
from conode_engine.gesture.one_euro import OneEuroFilter, OneEuroVec
from conode_engine.gesture.rules import eval_json_rules, recognize
from conode_engine.nodes.gesture_recognizer import GestureRecognizer
from conode_engine.nodes.hand_tracker import HandTracker
from conode_engine.nodes.live_diffusion import LiveDiffusion
from conode_engine.nodes.region_mask import RegionMask


def _hand(cx, cy, spread=0.1):
    pts = [[cx, cy, 0.0] for _ in range(21)]
    pts[0] = [cx, cy, 0.0]  # wrist
    pts[4] = [cx - spread, cy - spread, 0.0]  # thumb tip
    pts[8] = [cx + spread, cy - 2 * spread, 0.0]  # index tip (extended)
    pts[6] = [cx + 0.5 * spread, cy - spread, 0.0]  # index pip
    pts[12] = [cx, cy - 0.3 * spread, 0.0]  # middle tip (curled)
    pts[10] = [cx, cy - 0.6 * spread, 0.0]  # middle pip
    return [tuple(p) for p in pts]


# ---- one-euro ----
def test_one_euro_lags_step():
    f = OneEuroFilter(min_cutoff=0.5)
    f(0.0)
    y = f(1.0)
    assert 0.0 < y < 1.0  # 스텝을 지연/스무딩


def test_one_euro_vec_first_passthrough():
    assert OneEuroVec(2)([1.0, 2.0]) == [1.0, 2.0]


# ---- rules ----
def test_recognize_frame_two_hands():
    st = recognize([_hand(0.2, 0.5), _hand(0.8, 0.5)])
    assert st["type"] == "frame" and st["rect"] is not None
    x0, y0, x1, y1 = st["rect"]
    assert x0 < x1


def test_recognize_none():
    assert recognize([])["type"] == "none"


def test_recognize_single_hand():
    st = recognize([_hand(0.5, 0.5)])
    assert st["type"] in ("pinch", "point")
    assert 0.0 <= st["value"] <= 1.0


def test_json_rule_extended():
    rules = [
        {
            "name": "idx",
            "hand": 0,
            "when": [{"type": "extended", "finger": "index"}, {"type": "curled", "finger": "middle"}],
            "emit": {"type": "event", "event": "idx"},
        }
    ]
    st = eval_json_rules([_hand(0.5, 0.5)], rules)
    assert st is not None and st["event"] == "idx"


# ---- nodes ----
def test_hand_tracker_fallback():
    n = HandTracker("h")  # start() 미호출 → 폴백
    out = n.process(FrameCtx(), {"in": np.random.default_rng(0).integers(0, 255, (180, 320, 3), np.uint8)})
    assert out["hands"] == [] and out["w"] == 320
    assert n.preview_frame().shape == (180, 320, 3)


def test_gesture_recognizer_frame_and_preview():
    g = GestureRecognizer("g")
    packet = {"hands": [_hand(0.2, 0.5), _hand(0.8, 0.5)], "w": 320, "h": 180}
    st = g.process(FrameCtx(), {"hands": packet})
    assert st["type"] == "frame"
    assert g.preview_frame().shape == (180, 320, 3)


def test_region_mask_full_when_no_gesture():
    out = RegionMask("r").process(FrameCtx(), {"gesture": {"type": "none", "rect": None, "circle": None}})
    assert out.mean() > 200  # full white


def test_region_mask_rect():
    r = RegionMask("r")
    r.set("feather", 0)
    r.set("no_gesture", "none")
    out = r.process(FrameCtx(), {"gesture": {"type": "frame", "rect": (0.25, 0.25, 0.75, 0.75), "circle": None}})
    assert out[90, 160, 0] == 255  # 내부 흰색
    assert out[5, 5, 0] == 0  # 외부 검정


# ---- 통합: 프레임 제스처 = 영역 디퓨전 (§2 시그니처) ----
def test_frame_gesture_region_diffusion():
    region = RegionMask("region")
    region.set("feather", 0)
    region.set("no_gesture", "none")
    mask = region.process(FrameCtx(), {"gesture": {"type": "frame", "rect": (0.3, 0.3, 0.7, 0.7), "circle": None}})

    live = LiveDiffusion("live")
    live.start()
    live.set("advanced.similar_image_filter", False)
    img = np.random.default_rng(3).integers(0, 255, (180, 320, 3), np.uint8)
    out = live.process(FrameCtx(), {"in": img, "mask": mask})

    assert not np.array_equal(out[70:110, 140:180], img[70:110, 140:180])  # 내부 = 디퓨전
    assert np.array_equal(out[0:20, 0:20], img[0:20, 0:20])  # 외부 = 원본
