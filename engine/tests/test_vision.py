"""비전 노드 테스트 (T10/T11/T12) — 폴백 경로를 모델 없이 결정적으로 검증.

start()를 호출하지 않으므로 Pose/Segmentation 은 폴백으로 동작한다(모델 다운로드 불필요).
실모델 경로는 /live E2E 로 확인.
"""
from __future__ import annotations

import numpy as np

from conode_engine.core.graph import Graph
from conode_engine.core.processor import FrameCtx, Processor
from conode_engine.nodes.canny import Canny
from conode_engine.nodes.depth import Depth
from conode_engine.nodes.pose import Pose
from conode_engine.nodes.segmentation import Segmentation


def _frame():
    return np.random.default_rng(1).integers(0, 255, (180, 320, 3), dtype=np.uint8)


class _Src(Processor):
    inputs = ()

    def __init__(self, node_id, frame):
        super().__init__(node_id)
        self._frame = frame

    def process(self, ctx, inputs):
        return self._frame


def test_depth_outputs_bgr_frame():
    out = Depth("d").process(FrameCtx(), {"in": _frame()})
    assert out.shape == (180, 320, 3) and out.dtype == np.uint8


def test_depth_none_input():
    assert Depth("d").process(FrameCtx(), {"in": None}) is None


def test_pose_fallback_without_model():
    out = Pose("p").process(FrameCtx(), {"in": _frame()})
    assert out.shape == (180, 320, 3) and out.dtype == np.uint8


def test_segmentation_fallback_cutout():
    out = Segmentation("s").process(FrameCtx(), {"in": _frame()})
    assert out.shape == (180, 320, 3) and out.dtype == np.uint8


def test_segmentation_mask_mode():
    s = Segmentation("s")
    s.set("mode", "mask")
    out = s.process(FrameCtx(), {"in": _frame()})
    assert out.shape == (180, 320, 3)


def test_full_vision_graph_evaluates():
    g = Graph()
    g.add(_Src("cam", _frame()))
    for node in [Canny("canny"), Depth("depth"), Pose("pose"), Segmentation("seg")]:
        g.add(node)
        g.connect("cam", node.id, "in")
    g.evaluate(FrameCtx())
    for nid in ["canny", "depth", "pose", "seg"]:
        assert g.nodes[nid].output is not None
        assert g.nodes[nid].output.shape[:2] == (180, 320)
