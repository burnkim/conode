"""ModMatrix (M4, PLAN §3.3) — 제품의 심장.

소스(스템×특성 + LFO)를 타깃(modulatable 파라미터)에 라우팅. 셀: amount(-1..1),
curve(lin/exp/log), smooth(ms), clamp. 그래프와는 콜백으로 분리(테스트 용이).
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Callable, Optional


class LFO:
    def __init__(self, rate: float = 1.0, shape: str = "sine"):
        self.rate = rate
        self.shape = shape

    def value(self, t: float) -> float:
        phase = (t * self.rate) % 1.0
        if self.shape == "sine":
            return 0.5 + 0.5 * math.sin(2 * math.pi * phase)
        if self.shape == "tri":
            return 1.0 - abs(2 * phase - 1)
        if self.shape == "saw":
            return phase
        if self.shape == "square":
            return 1.0 if phase < 0.5 else 0.0
        return phase


def _curve(v: float, curve: str) -> float:
    if curve == "exp":
        return v * v
    if curve == "log":
        return math.sqrt(max(0.0, v))
    return v


@dataclass
class ModCell:
    source: str  # "stemN.feature" | "lfoN"
    target: str  # "nodeId.paramPath"
    amount: float = 1.0  # -1..1
    curve: str = "lin"
    smooth_ms: float = 50.0
    _smoothed: Optional[float] = field(default=None, repr=False)


class ModMatrix:
    def __init__(self):
        self.cells: list[ModCell] = []
        self.lfos: dict[str, LFO] = {}
        self._base: dict[str, float] = {}

    def add_cell(self, cell: ModCell) -> None:
        self.cells.append(cell)

    def add_lfo(self, name: str, lfo: LFO) -> None:
        self.lfos[name] = lfo

    # --- UI 편집 (매트릭스 에디터) ---
    def find_cell(self, source: str, target: str) -> Optional[ModCell]:
        for c in self.cells:
            if c.source == source and c.target == target:
                return c
        return None

    def set_cell(
        self, source: str, target: str, amount: float,
        curve: str = "lin", smooth_ms: float = 50.0,
    ) -> ModCell:
        """(source,target) 셀 upsert. 있으면 갱신, 없으면 추가."""
        cell = self.find_cell(source, target)
        if cell is None:
            cell = ModCell(source=source, target=target)
            self.cells.append(cell)
        cell.amount = float(amount)
        cell.curve = curve if curve in ("lin", "exp", "log") else "lin"
        cell.smooth_ms = max(0.0, float(smooth_ms))
        return cell

    def clear_cell(self, source: str, target: str) -> bool:
        cell = self.find_cell(source, target)
        if cell is None:
            return False
        self.cells.remove(cell)
        return True

    def cells_state(self) -> list[dict]:
        return [
            {
                "source": c.source, "target": c.target, "amount": c.amount,
                "curve": c.curve, "smooth_ms": c.smooth_ms,
            }
            for c in self.cells
        ]

    def resolve(self, source: str, features: dict, t: float) -> float:
        if source in self.lfos:
            return self.lfos[source].value(t)
        if "." in source:
            head, feat = source.split(".", 1)
            if head.startswith("stem"):
                try:
                    i = int(head[4:])
                except ValueError:
                    return 0.0
                stems = features.get("stems", []) if isinstance(features, dict) else []
                if 0 <= i < len(stems):
                    return float(stems[i].get(feat, 0.0))
            elif head == "gesture":  # 제스처 소스 (§3.3) — gesture.value/frame/point/pinch
                g = features.get("gesture", {}) if isinstance(features, dict) else {}
                if feat == "value":
                    return float(g.get("value") or 0.0)
                return 1.0 if g.get("type") == feat else 0.0
            elif head == "sig":  # 신호 노드 (LFO/EnvelopeFollower) — sig.<name>
                sigs = features.get("signals", {}) if isinstance(features, dict) else {}
                return float(sigs.get(feat, 0.0))
        return 0.0

    def apply(
        self,
        features: dict,
        t: float,
        dt: float,
        *,
        get: Callable[[str], float],
        set_: Callable[[str, float], None],
        rng: Callable[[str], tuple[float, float]],
        modulatable: Callable[[str], bool],
    ) -> dict[str, float]:
        """셀들을 평가해 타깃 파라미터를 base + 모듈레이션 으로 설정. 적용값 반환."""
        offsets: dict[str, float] = {}
        for cell in self.cells:
            if not modulatable(cell.target):  # R8: modulatable 만 타깃
                continue
            v = _curve(self.resolve(cell.source, features, t), cell.curve)
            a = 1.0 if cell.smooth_ms <= 0 else 1.0 - math.exp(-dt / (cell.smooth_ms / 1000.0))
            cell._smoothed = v if cell._smoothed is None else cell._smoothed + a * (v - cell._smoothed)
            lo, hi = rng(cell.target)
            offsets[cell.target] = offsets.get(cell.target, 0.0) + cell.amount * cell._smoothed * (hi - lo)
        applied = {}
        for target, off in offsets.items():
            if target not in self._base:
                self._base[target] = get(target)
            lo, hi = rng(target)
            val = min(hi, max(lo, self._base[target] + off))
            set_(target, val)
            applied[target] = val
        return applied

    def set_base(self, target: str, value: float) -> None:
        self._base[target] = value
