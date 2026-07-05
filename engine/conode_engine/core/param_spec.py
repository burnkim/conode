"""ParamSpec — 제품 전체의 척추 (PLAN §1.2).

단일 선언이 (a) UI 자동생성 (R2) (b) 모듈레이션 타깃 등록 (R8)
(c) OSC/MIDI 주소 (d) 직렬화를 모두 만든다. 위젯은 6종 고정 (R6):
Text · Slider(fill-bar) · Toggle · Enum · Seed · MultiMarkerSlider.
Group 은 위젯이 아니라 중첩 컨테이너(path = 'group.child').
"""
from __future__ import annotations

from typing import Any, Iterable


class ParamSpec:
    kind: str = "param"

    def __init__(self, default: Any, modulatable: bool = False):
        self.default = default
        self.modulatable = modulatable

    def coerce(self, value: Any) -> Any:
        """값을 검증·클램프해서 저장 가능한 형태로 반환."""
        return value

    def to_dict(self) -> dict:
        return {"kind": self.kind, "default": self.default, "modulatable": self.modulatable}


class Text(ParamSpec):
    kind = "text"

    def __init__(self, default: str = "", multiline: bool = False):
        super().__init__(str(default))
        self.multiline = multiline

    def coerce(self, value: Any) -> str:
        return str(value)

    def to_dict(self) -> dict:
        return {**super().to_dict(), "multiline": self.multiline}


class Slider(ParamSpec):
    kind = "slider"

    def __init__(
        self,
        lo: float,
        hi: float,
        default: float | None = None,
        modulatable: bool = False,
        integer: bool = False,
    ):
        self.lo = lo
        self.hi = hi
        self.integer = integer
        super().__init__(self._clamp(lo if default is None else default), modulatable)

    def _clamp(self, v: float):
        v = max(self.lo, min(self.hi, float(v)))
        return int(round(v)) if self.integer else v

    def coerce(self, value: Any):
        return self._clamp(value)

    def to_dict(self) -> dict:
        return {**super().to_dict(), "min": self.lo, "max": self.hi, "integer": self.integer}


class IntSlider(Slider):
    def __init__(self, lo: int, hi: int, default: int | None = None, modulatable: bool = False):
        super().__init__(lo, hi, default, modulatable, integer=True)


class Toggle(ParamSpec):
    kind = "toggle"

    def __init__(self, default: bool = False):
        super().__init__(bool(default))

    def coerce(self, value: Any) -> bool:
        return bool(value)


class Enum(ParamSpec):
    kind = "enum"

    def __init__(self, options: Iterable[str], default: str | None = None):
        self.options = list(options)
        if not self.options:
            raise ValueError("Enum needs at least one option")
        super().__init__(self.options[0] if default is None else default)

    def coerce(self, value: Any) -> str:
        if value not in self.options:
            raise ValueError(f"{value!r} not in {self.options}")
        return value

    def to_dict(self) -> dict:
        return {**super().to_dict(), "options": self.options}


class Seed(ParamSpec):
    kind = "seed"

    def __init__(self, mode: Iterable[str] = ("random", "fixed"), default: int = 0):
        self.modes = list(mode)
        super().__init__(int(default))

    def coerce(self, value: Any) -> int:
        return int(value)

    def to_dict(self) -> dict:
        return {**super().to_dict(), "modes": self.modes}


class MultiMarkerSlider(ParamSpec):
    kind = "multimarker"

    def __init__(self, lo: int, hi: int, markers: Iterable[int]):
        self.lo = lo
        self.hi = hi
        super().__init__(self._clamp(markers))

    def _clamp(self, markers: Iterable[int]) -> list[int]:
        return sorted(max(self.lo, min(self.hi, int(x))) for x in markers)

    def coerce(self, value: Any) -> list[int]:
        return self._clamp(value)

    def to_dict(self) -> dict:
        return {**super().to_dict(), "min": self.lo, "max": self.hi}


class Group:
    """중첩 파라미터 컨테이너 (§1.2). path 는 'group.child'."""

    kind = "group"

    def __init__(self, children: dict[str, "ParamSpec | Group"]):
        self.children = children

    def to_dict(self) -> dict:
        return {"kind": "group", "children": {k: v.to_dict() for k, v in self.children.items()}}


class ParamStore:
    """ParamSpec 선언을 path→spec 로 평탄화하고 현재 값을 보관."""

    def __init__(self, params: dict[str, "ParamSpec | Group"]):
        self._specs: dict[str, ParamSpec] = {}
        self._values: dict[str, Any] = {}
        self._flatten(params, prefix="")

    def _flatten(self, params: dict, prefix: str) -> None:
        for name, spec in params.items():
            path = f"{prefix}{name}"
            if isinstance(spec, Group):
                self._flatten(spec.children, prefix=f"{path}.")
            else:
                self._specs[path] = spec
                self._values[path] = spec.default

    def get(self, path: str) -> Any:
        return self._values[path]

    def set(self, path: str, value: Any) -> Any:
        if path not in self._specs:
            raise KeyError(path)
        self._values[path] = self._specs[path].coerce(value)
        return self._values[path]

    def paths(self) -> list[str]:
        return list(self._specs.keys())

    def modulation_targets(self) -> list[str]:
        """R8: modulatable 파라미터는 ModMatrix 타깃으로 자동 등록."""
        return [p for p, s in self._specs.items() if s.modulatable]

    def describe(self) -> dict:
        return {p: s.to_dict() for p, s in self._specs.items()}

    def values(self) -> dict:
        return dict(self._values)
