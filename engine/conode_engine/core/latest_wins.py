"""LatestWins — 최신 항목만 유지하는 버퍼 (PLAN §1.2).

무거운 노드(디퓨전)는 최신 프레임만 소비 → 프레임 드랍 허용, 지연 누적 금지.
"""
from __future__ import annotations

from typing import Generic, Optional, TypeVar

T = TypeVar("T")


class LatestWins(Generic[T]):
    __slots__ = ("_item", "_has", "_dropped")

    def __init__(self) -> None:
        self._item: Optional[T] = None
        self._has = False
        self._dropped = 0

    def put(self, item: T) -> None:
        if self._has:
            self._dropped += 1  # 소비되지 않은 이전 프레임을 버림
        self._item = item
        self._has = True

    def get(self) -> Optional[T]:
        if not self._has:
            return None
        item = self._item
        self._item = None
        self._has = False
        return item

    def peek(self) -> Optional[T]:
        return self._item if self._has else None

    @property
    def has(self) -> bool:
        return self._has

    @property
    def dropped(self) -> int:
        return self._dropped
