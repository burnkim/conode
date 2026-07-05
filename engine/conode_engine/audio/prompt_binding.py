"""프롬프트 바인딩 (M4, PLAN §3.3) — 인라인 문법 (token:{source}).

예: "(star:{kick.rms}), (geometric:{hats.flux})" → source 값으로 SD weight 치환:
"(star:0.72), (geometric:0.31)". resolve 콜백이 source→0..1 을 준다.
"""
from __future__ import annotations

import re
from typing import Callable

_BIND = re.compile(r"\(([^:(){}]+):\{([^}]+)\}\)")


def parse_bindings(template: str) -> list[tuple[str, str]]:
    """(token, source) 목록."""
    return [(m.group(1).strip(), m.group(2).strip()) for m in _BIND.finditer(template)]


def bind_prompt(template: str, resolve: Callable[[str], float]) -> str:
    def repl(m: re.Match) -> str:
        token = m.group(1).strip()
        w = max(0.0, min(2.0, float(resolve(m.group(2).strip()))))
        return f"({token}:{w:.2f})"

    return _BIND.sub(repl, template)
