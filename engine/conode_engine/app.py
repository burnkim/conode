"""conode-engine 실행 진입 (T6/T8).

그래프: Camera → Canny. 매 tick 위상 평가 후, output 이 있는 모든 노드의 프리뷰를
frame.preview 로 브로드캐스트한다. fps 는 실측(EMA), ms 는 노드별 처리시간.
PLAN §1.1 프레임 전송(프리뷰는 다운샘플 JPEG over WS).
"""
from __future__ import annotations

import asyncio
import time

import websockets

from .core.graph import Graph
from .core.preview import encode_jpeg, frame_size
from .core.processor import FrameCtx
from .nodes.audio_in import AudioIn
from .nodes.camera import Camera
from .nodes.canny import Canny
from .nodes.gesture_recognizer import GestureRecognizer
from .nodes.hand_tracker import HandTracker
from .nodes.live_diffusion import LiveDiffusion
from .nodes.mod_matrix import ModMatrix
from .nodes.region_mask import RegionMask
from .protocol.messages import FramePreview
from .protocol.server import EngineServer


def build_graph() -> tuple[Graph, Camera]:
    # M3 제스처=영역 디퓨전 (§2) + M4 오디오 ModMatrix (§3)
    cam = Camera("cam1", index=1)
    canny = Canny("canny1", index=2)
    hands = HandTracker("hands1", index=3)
    gesture = GestureRecognizer("gesture1", index=4)
    region = RegionMask("region1", index=5)
    live = LiveDiffusion("live1", index=6)
    audio = AudioIn("audio1", index=7)
    mod = ModMatrix("mod1", index=8)
    graph = Graph()
    for n in (cam, canny, hands, gesture, region, live, audio, mod):
        graph.add(n)
    graph.connect("cam1", "canny1", "in")
    graph.connect("cam1", "hands1", "in")
    graph.connect("hands1", "gesture1", "hands")
    graph.connect("gesture1", "region1", "gesture")
    graph.connect("cam1", "live1", "in")
    graph.connect("canny1", "live1", "control")  # ControlNet
    graph.connect("region1", "live1", "mask")  # 제스처 영역만 디퓨전
    graph.connect("audio1", "mod1", "audio")  # 오디오 특성 → ModMatrix
    mod.graph = graph  # ModMatrix 는 그래프 파라미터를 모듈레이션
    return graph, cam


async def run(host: str = "127.0.0.1", port: int = 8787, target_fps: float = 30.0) -> None:
    graph, cam = build_graph()
    for node in graph.nodes.values():
        node.start()  # 캡처 스레드/모델 로드 등 무거운 준비 (R4: tick 밖)
    server = EngineServer(graph=graph, host=host, port=port)
    period = 1.0 / target_fps

    async def broadcaster() -> None:
        ema_fps = 0.0
        last = time.monotonic()
        seq = 0
        logged_first = False
        while True:
            t0 = time.monotonic()
            if server.clients:
                graph.evaluate(FrameCtx(seq=seq, t=t0))
                now = time.monotonic()
                dt = now - last
                last = now
                inst = 1.0 / dt if dt > 0 else 0.0
                ema_fps = inst if ema_fps == 0.0 else ema_fps * 0.9 + inst * 0.1
                seq += 1
                for node in list(graph.nodes.values()):  # 그래프 편집 중 안전 순회
                    pf = node.preview_frame()
                    payload = encode_jpeg(pf)
                    if payload is None:
                        continue
                    w, h = frame_size(pf)
                    await server.broadcast(
                        FramePreview(
                            node=node.id,
                            w=w,
                            h=h,
                            fps=round(ema_fps, 1),
                            ms=round(node.last_ms, 1),
                            format="jpeg",
                            seq=seq,
                            data=payload,
                        )
                    )
                if not logged_first and cam.output is not None:
                    src = "camera" if cam.is_real else "synthetic"
                    print(f"first frame · source={src} · {cam.width}x{cam.height}", flush=True)
                    logged_first = True
            else:
                last = time.monotonic()  # 유휴 후 첫 프레임 dt 폭주 방지
            elapsed = time.monotonic() - t0
            await asyncio.sleep(max(0.0, period - elapsed))

    async with websockets.serve(server.handler, host, port):
        nodes = "+".join(n.id for n in graph.nodes.values())
        print(f"conode-engine  ws://{host}:{port}  (graph: cam1→[{nodes}], probing camera…)", flush=True)
        try:
            await broadcaster()
        finally:
            for node in graph.nodes.values():
                node.stop()


def main() -> None:
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
