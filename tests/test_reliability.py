
import json

import pytest

from app import reliability


def test_reliability_aggregation(tmp_path, monkeypatch):
    history = tmp_path / "history"
    history.mkdir()

    monkeypatch.setattr(reliability, "HISTORY", history)
    monkeypatch.setattr(reliability, "REPORTS", tmp_path)

    samples = [
        ("001", True, 100, 1.0),
        ("002", True, 200, 2.0),
        ("003", False, 400, 4.0),
    ]

    for run_id, success, tokens, duration in samples:
        report = {
            "run_id": run_id,
            "benchmark": "inventory_case",
            "model": "test-model",
            "success": success,
            "tokens_used": tokens,
            "duration_seconds": duration,
            "trajectory": [],
        }

        (history / f"{run_id}.json").write_text(
            json.dumps(report),
            encoding="utf-8",
        )

    results = reliability.analyze_reliability(
        "inventory_case",
        recent=2,
    )

    assert len(results) == 1

    result = results[0]

    assert result["trials"] == 2
    assert result["successful_trials"] == 1
    assert result["success_rate_percent"] == 50.0
    assert result["average_tokens"] == 300
    assert result["average_duration_seconds"] == 3.0
    assert result["duration_stddev_seconds"] == pytest.approx(
        1.414, abs=0.001
    )
