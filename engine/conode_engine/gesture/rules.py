"""제스처 규칙 (M3, PLAN §2) — 규칙 기반 v1 + JSON 규칙 확장(ComfyUI 대비 차별점).

입력 hands: 손 리스트, 각 손 = 21×(x,y,z) 정규화 좌표(0..1). MediaPipe Hand 토폴로지.
recognize() 는 내장 제스처를, eval_json_rules() 는 사용자 JSON 규칙을 평가한다.
"""
from __future__ import annotations

import math
from typing import Optional, Sequence

# 랜드마크 인덱스 (MediaPipe Hand 21점)
LM = {
    "wrist": 0,
    "thumb_cmc": 1, "thumb_mcp": 2, "thumb_ip": 3, "thumb_tip": 4,
    "index_mcp": 5, "index_pip": 6, "index_dip": 7, "index_tip": 8,
    "middle_mcp": 9, "middle_pip": 10, "middle_dip": 11, "middle_tip": 12,
    "ring_mcp": 13, "ring_pip": 14, "ring_dip": 15, "ring_tip": 16,
    "pinky_mcp": 17, "pinky_pip": 18, "pinky_dip": 19, "pinky_tip": 20,
}
_FINGER = {  # (tip, pip)
    "thumb": (4, 2), "index": (8, 6), "middle": (12, 10), "ring": (16, 14), "pinky": (20, 18),
}

DEFAULT_CFG = {
    "pinch_min": 0.02,
    "pinch_max": 0.20,
    "point_radius": 0.12,
    "palm_size_trigger": 0.55,
}

Hand = Sequence[Sequence[float]]


def _dist(a, b) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def _clamp01(v: float) -> float:
    return max(0.0, min(1.0, v))


def _extended(hand: Hand, finger: str) -> bool:
    tip, pip = _FINGER[finger]
    return _dist(hand[tip], hand[LM["wrist"]]) > _dist(hand[pip], hand[LM["wrist"]])


def _hand_span(hand: Hand) -> float:
    xs = [p[0] for p in hand]
    ys = [p[1] for p in hand]
    return math.hypot(max(xs) - min(xs), max(ys) - min(ys))


def _blank_state() -> dict:
    return {"type": "none", "rect": None, "circle": None, "value": None, "event": None, "hands": 0}


def recognize(hands: Sequence[Hand], cfg: Optional[dict] = None) -> dict:
    c = {**DEFAULT_CFG, **(cfg or {})}
    st = _blank_state()
    st["hands"] = len(hands)
    if not hands:
        return st

    if len(hands) >= 2:
        # frame — 양손 thumb+index 코너로 사각형 (§2 프레임 제스처)
        h1, h2 = hands[0], hands[1]
        pts = [h1[4], h1[8], h2[4], h2[8]]
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        st["type"] = "frame"
        st["rect"] = (min(xs), min(ys), max(xs), max(ys))
        return st

    h = hands[0]
    pinch = _dist(h[4], h[8])
    st["value"] = _clamp01((pinch - c["pinch_min"]) / (c["pinch_max"] - c["pinch_min"]))
    if _hand_span(h) > c["palm_size_trigger"]:
        st["event"] = "palm_push"
    if _extended(h, "index") and not _extended(h, "middle") and not _extended(h, "ring"):
        # point — 검지 포인팅 → 원형 마스크 (point-hold 는 노드가 지속시간 처리)
        st["type"] = "point"
        st["circle"] = (h[8][0], h[8][1], c["point_radius"])
    else:
        st["type"] = "pinch"
    return st


# ---------- JSON 규칙 확장 ----------
def _cond_ok(hand: Hand, cond: dict) -> bool:
    t = cond.get("type")
    if t == "extended":
        return _extended(hand, cond["finger"])
    if t == "curled":
        return not _extended(hand, cond["finger"])
    if t == "dist":
        d = _dist(hand[cond["a"]], hand[cond["b"]])
        op, v = cond["op"], float(cond["value"])
        return (d < v) if op == "<" else (d > v) if op == ">" else False
    return False


def eval_json_rules(hands: Sequence[Hand], rules: Sequence[dict]) -> Optional[dict]:
    """사용자 정의 JSON 규칙 평가. 첫 매칭 규칙의 emit 을 gesture state 로 반환.
    규칙: {name, hand, when:[{type:dist|extended|curled,...}], emit:{type, event?/circle?}}."""
    for rule in rules:
        hi = int(rule.get("hand", 0))
        if hi >= len(hands):
            continue
        hand = hands[hi]
        if all(_cond_ok(hand, c) for c in rule.get("when", [])):
            emit = rule.get("emit", {})
            st = _blank_state()
            st["hands"] = len(hands)
            st["type"] = emit.get("type", rule.get("name", "custom"))
            st["event"] = emit.get("event")
            if emit.get("at_landmark") is not None:
                p = hand[int(emit["at_landmark"])]
                st["circle"] = (p[0], p[1], float(emit.get("radius", 0.12)))
            return st
    return None
