"""MappedOutput 노드 (M5, PLAN §4) — 코너핀 4점 homography 워프 + 엣지 블렌드.

입력 프레임의 4모서리를 정규화 코너(corners.*)로 매핑해 출력 캔버스에 워프한다.
v1 = 단일 서피스 코너핀. 실전 출력(전용창/NDI/Spout)은 T33(네이티브). 여긴 프레임 워프.
"""
from __future__ import annotations

from typing import Optional

import cv2
import numpy as np

from ..core.param_spec import Group, IntSlider, Slider
from ..core.processor import FrameCtx, Processor


class MappedOutput(Processor):
    category = "output"
    name = "MappedOutput"
    kind = "mapped_output"
    inputs = ("in",)
    params = {
        "out_w": IntSlider(64, 1920, default=320),
        "out_h": IntSlider(64, 1080, default=180),
        "edge_blend": Slider(0.0, 0.5, default=0.0),
        # 코너핀: 4모서리 정규화 좌표 (기본 = 전체 프레임)
        "corners": Group(
            {
                "tl_x": Slider(0.0, 1.0, default=0.0), "tl_y": Slider(0.0, 1.0, default=0.0),
                "tr_x": Slider(0.0, 1.0, default=1.0), "tr_y": Slider(0.0, 1.0, default=0.0),
                "br_x": Slider(0.0, 1.0, default=1.0), "br_y": Slider(0.0, 1.0, default=1.0),
                "bl_x": Slider(0.0, 1.0, default=0.0), "bl_y": Slider(0.0, 1.0, default=1.0),
            }
        ),
    }

    def process(self, ctx: FrameCtx, inputs: dict) -> Optional[np.ndarray]:
        src = inputs.get("in")
        if src is None:
            return None
        sh, sw = src.shape[:2]
        ow = int(self.get("out_w"))
        oh = int(self.get("out_h"))
        src_pts = np.float32([[0, 0], [sw, 0], [sw, sh], [0, sh]])
        g = self.get
        dst_pts = np.float32(
            [
                [g("corners.tl_x") * ow, g("corners.tl_y") * oh],
                [g("corners.tr_x") * ow, g("corners.tr_y") * oh],
                [g("corners.br_x") * ow, g("corners.br_y") * oh],
                [g("corners.bl_x") * ow, g("corners.bl_y") * oh],
            ]
        )
        h = cv2.getPerspectiveTransform(src_pts, dst_pts)
        out = cv2.warpPerspective(src, h, (ow, oh), flags=cv2.INTER_LINEAR, borderValue=(0, 0, 0))

        blend = float(self.get("edge_blend"))
        if blend > 0:
            out = self._edge_blend(out, blend)
        return out

    def _edge_blend(self, img: np.ndarray, amount: float) -> np.ndarray:
        h, w = img.shape[:2]
        bw = max(1, int(w * amount))
        bh = max(1, int(h * amount))
        ramp_x = np.ones(w, np.float32)
        ramp_x[:bw] = np.linspace(0, 1, bw)
        ramp_x[w - bw :] = np.linspace(1, 0, bw)
        ramp_y = np.ones(h, np.float32)
        ramp_y[:bh] = np.linspace(0, 1, bh)
        ramp_y[h - bh :] = np.linspace(1, 0, bh)
        mask = np.outer(ramp_y, ramp_x)[:, :, None]
        return (img.astype(np.float32) * mask).astype(np.uint8)
