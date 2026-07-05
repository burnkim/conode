"""라이선스 (M6, PLAN §7) — Ed25519 서명 라이선스 파일, 오프라인 활성화.

발급자(비공개키)가 서명 → 클라이언트(공개키)가 로컬 검증. 서버 불필요(공연장 인터넷 없음
전제). 크랙 방어에 과투자하지 않음 — 가치는 업데이트/프리셋 생태계. 실검증은 Tauri Rust
사이드에서도 미러(동일 포맷). 여긴 발급/검증 로직 + CLI.

CLI:
  python -m conode_engine.licensing keygen                 # 키쌍 출력
  python -m conode_engine.licensing issue --name .. --tier pro --pub <hex> --priv <hex>
  python -m conode_engine.licensing verify <license> --pub <hex>
"""
from __future__ import annotations

import argparse
import base64
import json
import sys
from typing import Optional

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)

TIERS = {
    "personal": {"seats": 1, "commercial": False, "outputs": ["file"]},
    "pro": {"seats": 2, "commercial": True, "outputs": ["file", "ndi", "spout", "syphon"]},
    "edu": {"seats": 1, "commercial": False, "outputs": ["file"], "discount": True},
}


def generate_keypair() -> tuple[str, str]:
    """(priv_hex, pub_hex) — 발급자 보관용 개인키 + 앱 임베드용 공개키."""
    priv = Ed25519PrivateKey.generate()
    from cryptography.hazmat.primitives import serialization

    priv_raw = priv.private_bytes(
        serialization.Encoding.Raw,
        serialization.PrivateFormat.Raw,
        serialization.NoEncryption(),
    )
    pub_raw = priv.public_key().public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw
    )
    return priv_raw.hex(), pub_raw.hex()


def _canon(payload: dict) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()


def issue_license(payload: dict, priv_hex: str) -> str:
    priv = Ed25519PrivateKey.from_private_bytes(bytes.fromhex(priv_hex))
    tier = payload.get("tier", "personal")
    full = {**TIERS.get(tier, {}), **payload}
    sig = priv.sign(_canon(full))
    lic = {"payload": full, "sig": base64.b64encode(sig).decode()}
    return base64.b64encode(json.dumps(lic).encode()).decode()


def verify_license(license_str: str, pub_hex: str) -> Optional[dict]:
    """유효하면 payload, 아니면 None. 오프라인·로컬 검증."""
    try:
        pub = Ed25519PublicKey.from_public_bytes(bytes.fromhex(pub_hex))
        lic = json.loads(base64.b64decode(license_str))
        pub.verify(base64.b64decode(lic["sig"]), _canon(lic["payload"]))
        return lic["payload"]
    except (InvalidSignature, ValueError, KeyError, json.JSONDecodeError):
        return None


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="conode_engine.license")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("keygen")
    pi = sub.add_parser("issue")
    pi.add_argument("--name", required=True)
    pi.add_argument("--email", default="")
    pi.add_argument("--tier", default="personal", choices=list(TIERS))
    pi.add_argument("--priv", required=True)
    pv = sub.add_parser("verify")
    pv.add_argument("license")
    pv.add_argument("--pub", required=True)
    args = ap.parse_args(argv)

    if args.cmd == "keygen":
        priv, pub = generate_keypair()
        print(f"priv (발급자 보관): {priv}\npub  (앱 임베드): {pub}")
    elif args.cmd == "issue":
        lic = issue_license({"name": args.name, "email": args.email, "tier": args.tier}, args.priv)
        print(lic)
    elif args.cmd == "verify":
        payload = verify_license(args.license, args.pub)
        if payload is None:
            print("INVALID")
            return 1
        print(f"VALID · {json.dumps(payload, ensure_ascii=False)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
