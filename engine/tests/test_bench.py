"""벤치 하네스 테스트 (T20) — 포터블 노드로 측정 동작 확인."""
from __future__ import annotations

import pytest

from conode_engine.bench import BUDGET_MS, bench_node, main


def test_bench_canny_reports_metrics():
    r = bench_node("canny", frames=20)
    assert r["fps"] > 0
    assert r["mean_ms"] >= 0
    assert r["budget_ms"] == BUDGET_MS["canny"]


def test_bench_unknown_node_raises():
    with pytest.raises(ValueError):
        bench_node("nope", frames=2)


def test_bench_main_runs_report_only():
    # 예산 초과해도 --enforce 없으면 0
    assert main(["canny", "--frames", "10"]) == 0
