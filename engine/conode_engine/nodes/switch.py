"""Switch 노드 (M-B, PLAN §1.3 Logic) — 입력 4개 중 select 하나를 통과."""
from __future__ import annotations

from typing import Optional

import numpy as np

from ..core.param_spec import IntSlider
from ..core.processor import FrameCtx, Processor


class Switch(Processor):
    category = "generate"
    name = "Switch"
    kind = "switch"
    inputs = ("in0", "in1", "in2", "in3")
    params = {
        "select": IntSlider(0, 3, default=0, modulatable=True),  # 오디오/제스처로 씬 전환
    }

    def process(self, ctx: FrameCtx, inputs: dict) -> Optional[np.ndarray]:
        return inputs.get(f"in{int(self.get('select'))}")
