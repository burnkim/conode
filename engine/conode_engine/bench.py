"""노드 성능 벤치 (M2 T20) — CLAUDE.md 검증: `python -m conode_engine.bench <node>`.

노드를 N 프레임 tick 하여 fps/ms 를 측정하고 PLAN §6 예산표와 비교한다.
--enforce 시 예산 초과하면 exit 1 (예산은 4090/640x480 목표 — Mac 개발기에선 참고용).
포터블: canny/depth/live_diffusion(fallback) 은 Mac 에서도 측정 가능.
"""
from __future__ import annotations

import argparse
import sys
import time

import numpy as np

from .core.processor import FrameCtx
from .protocol.server import node_registry

# PLAN §6 예산 (RTX 4090 / 640x480 목표, ms/frame)
BUDGET_MS = {
    "camera": 2.0,
    "canny": 1.0,
    "pose": 4.0,
    "depth": 6.0,
    "segmentation": 5.0,
    "live_diffusion": 35.0,
}


def bench_node(kind: str, frames: int = 120, w: int = 320, h: int = 180) -> dict:
    reg = node_registry()
    cls = reg.get(kind)
    if cls is None:
        raise ValueError(f"unknown node: {kind} (have: {', '.join(reg)})")
    node = cls(f"{kind}_bench")
    node.start()
    inp = np.random.default_rng(0).integers(0, 255, (h, w, 3), dtype=np.uint8)
    args = {"in": inp} if node.inputs else {}
    for _ in range(5):  # warmup
        node.tick(FrameCtx(), args)
    samples = []
    t0 = time.perf_counter()
    for i in range(frames):
        node.tick(FrameCtx(seq=i), args)
        samples.append(node.last_ms)
    dt = time.perf_counter() - t0
    node.stop()
    return {
        "kind": kind,
        "frames": frames,
        "fps": frames / dt if dt > 0 else 0.0,
        "mean_ms": sum(samples) / len(samples) if samples else 0.0,
        "budget_ms": BUDGET_MS.get(kind),
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="conode_engine.bench")
    ap.add_argument("node", help="node kind, or 'all'")
    ap.add_argument("--frames", type=int, default=120)
    ap.add_argument("--size", default="320x180")
    ap.add_argument("--enforce", action="store_true", help="예산 초과 시 exit 1 (4090 목표)")
    args = ap.parse_args(argv)
    w, h = (int(x) for x in args.size.split("x"))
    kinds = list(node_registry()) if args.node == "all" else [args.node]

    over = []
    for k in kinds:
        try:
            r = bench_node(k, args.frames, w, h)
        except Exception as e:  # noqa: BLE001
            print(f"{k:16} ERROR {e}")
            continue
        b = r["budget_ms"]
        flag = ""
        if b is not None and r["mean_ms"] > b:
            flag = f"  OVER §6 budget {b}ms (4090 목표)"
            over.append(k)
        bstr = f"{b}ms" if b is not None else "—"
        print(f"{k:16} {r['fps']:7.1f} fps  {r['mean_ms']:7.2f} ms/frame  (budget {bstr}){flag}")

    if args.enforce and over:
        print(f"\nFAIL: {len(over)} node(s) over §6 budget: {', '.join(over)}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
