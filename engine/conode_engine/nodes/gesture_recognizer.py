"""GestureRecognizer 노드 (M3, PLAN §2) — 규칙 기반 v1 제스처.

입력: HandTracker output(hands). 출력: gesture state(dict) — type/rect/circle/value/event.
point-hold 지속시간·palm-push 엣지는 노드가 시간 상태로 처리. preview = 인식 주석.
"""
from __future__ import annotations

from typing import Optional

import cv2
import numpy as np

from ..core.param_spec import Slider, Toggle
from ..core.processor import FrameCtx, Processor
from ..gesture.rules import recognize


class GestureRecognizer(Processor):
    category = "depth"  # Analysis (blue)
    name = "GestureRecognizer"
    kind = "gesture_recognizer"
    inputs = ("hands",)
    params = {
        "pinch_min": Slider(0.0, 0.2, default=0.02),
        "pinch_max": Slider(0.05, 0.4, default=0.2),
        "point_hold_sec": Slider(0.5, 3.0, default=1.5),
        "palm_size_trigger": Slider(0.3, 0.9, default=0.55),
        "annotate": Toggle(True),
    }

    def __init__(self, node_id: str = "gesture1", index: int = 0):
        super().__init__(node_id, index)
        self._point_start: Optional[float] = None
        self._palm_active = False

    def process(self, ctx: FrameCtx, inputs: dict) -> Optional[dict]:
        packet = inputs.get("hands")
        hands = packet.get("hands", []) if isinstance(packet, dict) else []
        w = packet.get("w", 320) if isinstance(packet, dict) else 320
        h = packet.get("h", 180) if isinstance(packet, dict) else 180

        cfg = {
            "pinch_min": float(self.get("pinch_min")),
            "pinch_max": float(self.get("pinch_max")),
            "palm_size_trigger": float(self.get("palm_size_trigger")),
        }
        state = recognize(hands, cfg)

        # point-hold: 검지 포인팅을 point_hold_sec 이상 유지 → 이벤트
        if state["type"] == "point":
            if self._point_start is None:
                self._point_start = ctx.t
            elif ctx.t - self._point_start >= float(self.get("point_hold_sec")):
                state["event"] = "point_hold"
        else:
            self._point_start = None

        # palm-push: 라이징 엣지에서만 이벤트 (매 프레임 반복 방지)
        if state.get("event") == "palm_push":
            if self._palm_active:
                state["event"] = None  # 이미 활성 — 중복 억제
            self._palm_active = True
        else:
            self._palm_active = False

        if self.get("annotate"):
            self.preview = self._annotate(w, h, state)
        return state

    def _annotate(self, w: int, h: int, state: dict) -> np.ndarray:
        canvas = np.zeros((h, w, 3), np.uint8)
        col = (156, 199, 242)  # cat-depth
        if state.get("rect"):
            x0, y0, x1, y1 = state["rect"]
            cv2.rectangle(canvas, (int(x0 * w), int(y0 * h)), (int(x1 * w), int(y1 * h)), col, 2)
        if state.get("circle"):
            cx, cy, r = state["circle"]
            cv2.circle(canvas, (int(cx * w), int(cy * h)), int(r * min(w, h)), col, 2)
        label = state["type"]
        if state.get("event"):
            label += f" · {state['event']}"
        cv2.putText(canvas, label, (8, h - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, col, 1, cv2.LINE_AA)
        return canvas
