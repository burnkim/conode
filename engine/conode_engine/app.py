"""conode-engine 실행 진입 (T6).

Camera 노드를 캡처 스레드로 돌리고, WS 서버에 붙은 UI 로 frame.preview 를
브로드캐스트한다. fps/ms 는 실측(EMA) — UI NodeCard 배지가 이 값을 표시.
PLAN §1.1 프레임 전송(프리뷰는 다운샘플 JPEG over WS).
"""
from __future__ import annotations

import asyncio
import time

import websockets

from .core.processor import FrameCtx
from .nodes.camera import Camera
from .protocol.messages import FramePreview
from .protocol.server import EngineServer


async def run(host: str = "127.0.0.1", port: int = 8787, target_fps: float = 30.0) -> None:
    cam = Camera("cam1", index=1)
    cam.start()
    server = EngineServer(nodes=[cam], host=host, port=port)
    period = 1.0 / target_fps

    async def broadcaster() -> None:
        ema_fps = 0.0
        last = time.monotonic()
        seq = 0
        logged_first = False
        while True:
            t0 = time.monotonic()
            # 클라이언트 없으면 인코딩도 스킵 (CPU 절약)
            if server.clients:
                payload = cam.tick(FrameCtx(seq=seq))
                if payload is not None:
                    if not logged_first:
                        # is_real 은 첫 프레임 시점에 확정 (권한 그랜트 후) — 정확히 로깅
                        src = "camera" if cam.is_real else "synthetic"
                        print(f"first frame · source={src} · {cam.width}x{cam.height}", flush=True)
                        logged_first = True
                    now = time.monotonic()
                    dt = now - last
                    last = now
                    inst = 1.0 / dt if dt > 0 else 0.0
                    ema_fps = inst if ema_fps == 0.0 else ema_fps * 0.9 + inst * 0.1
                    ms = (time.monotonic() - t0) * 1000.0
                    seq += 1
                    await server.broadcast(
                        FramePreview(
                            node="cam1",
                            w=cam.width,
                            h=cam.height,
                            fps=round(ema_fps, 1),
                            ms=round(ms, 1),
                            format="jpeg",
                            seq=seq,
                            data=payload,
                        )
                    )
            else:
                last = time.monotonic()  # 유휴 후 첫 프레임의 dt 폭주 방지
            elapsed = time.monotonic() - t0
            await asyncio.sleep(max(0.0, period - elapsed))

    async with websockets.serve(server.handler, host, port):
        # 카메라 권한 그랜트가 첫 cap.read() 를 블록할 수 있어, 소스 확정은
        # broadcaster 의 첫 프레임 로그에서 (여기선 리슨만 알림).
        print(f"conode-engine  ws://{host}:{port}  (probing camera…)", flush=True)
        try:
            await broadcaster()
        finally:
            cam.stop()


def main() -> None:
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
