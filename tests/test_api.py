
import json

from fastapi.testclient import TestClient

from app import main as api

client = TestClient(api.app)


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_benchmarks_endpoint():
    response = client.get("/api/benchmarks")

    assert response.status_code == 200

    names = {item["name"] for item in response.json()}

    assert {
        "pricing_case",
        "pagination_case",
        "inventory_case",
    }.issubset(names)


def test_empty_experiment_history(tmp_path, monkeypatch):
    monkeypatch.setattr(api, "REPORTS", tmp_path)

    response = client.get("/api/experiments")

    assert response.status_code == 200
    assert response.json() == []


def test_missing_comparison_report(tmp_path, monkeypatch):
    monkeypatch.setattr(api, "REPORTS", tmp_path)

    response = client.get("/api/comparison")

    assert response.status_code == 404


def test_heldout_endpoint(tmp_path, monkeypatch):
    monkeypatch.setattr(api, "REPORTS", tmp_path)

    sample = {
        "run_id": "test_run_001",
        "benchmark": "inventory_case",
        "model": "openai/gpt-oss-20b",
        "public_success": True,
        "heldout_evaluation": {
            "success": True,
            "passed": 4,
            "failed": 0,
            "total": 4,
        },
    }

    report = tmp_path / "test_run_001_heldout.json"
    report.write_text(
        json.dumps(sample),
        encoding="utf-8",
    )

    response = client.get("/api/heldout")

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["heldout_success"] is True
    assert response.json()[0]["passed"] == 4
