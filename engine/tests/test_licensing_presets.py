"""라이선스 + 프리셋 테스트 (M6, T34/T35)."""
from __future__ import annotations

import base64
import json
from pathlib import Path

import pytest

from conode_engine.licensing import generate_keypair, issue_license, verify_license
from conode_engine.protocol.server import node_registry

_PRESETS = sorted((Path(__file__).resolve().parents[2] / "presets").glob("*.json"))


# ---- 라이선스 (Ed25519, 오프라인) ----
def test_license_roundtrip_and_tier_merge():
    priv, pub = generate_keypair()
    lic = issue_license({"name": "Alice", "tier": "pro"}, priv)
    payload = verify_license(lic, pub)
    assert payload is not None
    assert payload["name"] == "Alice" and payload["tier"] == "pro"
    assert payload["seats"] == 2 and payload["commercial"] is True  # 티어 기본 병합


def test_license_tamper_rejected():
    priv, pub = generate_keypair()
    lic = issue_license({"name": "Bob", "tier": "personal"}, priv)
    d = json.loads(base64.b64decode(lic))
    d["payload"]["tier"] = "pro"  # 위조
    tampered = base64.b64encode(json.dumps(d).encode()).decode()
    assert verify_license(tampered, pub) is None


def test_license_wrong_key_rejected():
    priv, _ = generate_keypair()
    _, other_pub = generate_keypair()
    lic = issue_license({"name": "C", "tier": "edu"}, priv)
    assert verify_license(lic, other_pub) is None


# ---- 프리셋 팩 ----
def test_presets_exist():
    assert len(_PRESETS) >= 2


@pytest.mark.parametrize("path", _PRESETS, ids=lambda p: p.name)
def test_preset_valid(path):
    data = json.loads(path.read_text())
    reg = node_registry()
    ids = {n["id"] for n in data["nodes"]}
    for n in data["nodes"]:
        assert n["node_type"] in reg, f"{n['node_type']} not in registry"
    for e in data["edges"]:
        assert e["src"] in ids and e["dst"] in ids
        dst_type = next(n["node_type"] for n in data["nodes"] if n["id"] == e["dst"])
        assert e["port"] in reg[dst_type].inputs, f"{dst_type} has no input {e['port']}"
