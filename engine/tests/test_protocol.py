"""프로토콜 계약 테스트 (T4) — packages/schema/examples.json 공유 픽스처.

zod(TS) 쪽 apps/studio/src/lib/protocol/messages.test.ts 와 동일 픽스처를 검증한다.
둘 다 통과해야 UI↔엔진 계약이 성립 (R3).
"""
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from conode_engine.protocol.messages import (
    PROTOCOL_VERSION,
    FramePreview,
    Hello,
    parse_message,
)

_EXAMPLES = json.loads(
    (Path(__file__).resolve().parents[2] / "packages" / "schema" / "examples.json").read_text()
)


@pytest.mark.parametrize("msg", _EXAMPLES["valid"], ids=lambda m: f'{m["type"]}')
def test_valid_messages_parse(msg):
    parsed = parse_message(msg)
    assert parsed.type == msg["type"]


@pytest.mark.parametrize("msg", _EXAMPLES["invalid"], ids=lambda m: f'{m.get("type", "?")}')
def test_invalid_messages_rejected(msg):
    with pytest.raises(ValidationError):
        parse_message(msg)


def test_protocol_version_is_zero():
    assert PROTOCOL_VERSION == 0


def test_frame_preview_roundtrip():
    fp = FramePreview(node="cam1", w=320, h=240, fps=30.0, ms=5.0, format="jpeg", seq=1, data="AA")
    assert parse_message(fp.model_dump()) == fp


def test_hello_defaults_type_and_version():
    h = Hello(role="engine")
    assert h.type == "hello"
    assert h.v == 0
