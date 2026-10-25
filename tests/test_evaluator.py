"""Unit tests for the benchmark scorer; no Docker or API calls required."""
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from app import evaluator


@pytest.fixture
def pricing_names():
    cfg = evaluator.BENCHMARKS["pricing_case"]
    return cfg["fail_to_pass"] + cfg["pass_to_pass"]


def mock_pytest(monkeypatch, cases, returncode=None):
    """Supply synthetic JUnit XML to the scorer instead of running Pytest."""

    def fake_run(command, **kwargs):
        xml_option = next(
            item for item in command if item.startswith("--junitxml=")
        )
        xml_path = Path(xml_option.split("=", 1)[1])
        suite = ET.Element("testsuite")
        for name, status in cases:
            node = ET.SubElement(suite, "testcase", name=name)
            if status != "passed":
                ET.SubElement(node, status)
        ET.ElementTree(suite).write(xml_path, encoding="utf-8")
        code = (
            returncode if returncode is not None
            else int(any(status != "passed" for _, status in cases))
        )
        return subprocess.CompletedProcess(command, code, stdout="", stderr="")

    monkeypatch.setattr(evaluator.subprocess, "run", fake_run)


def test_all_registered_tests_pass(tmp_path, monkeypatch, pricing_names):
    monkeypatch.setattr(evaluator, "REPORTS", tmp_path)
    mock_pytest(monkeypatch, [(n, "passed") for n in pricing_names])

    result = evaluator.run_evaluation("pricing_case")
    assert result["total"] == 4
    assert result["passed"] == 4
    assert result["failed"] == 0
    assert result["errors"] == 0
    assert result["skipped"] == 0


def test_skips_and_errors_are_not_successes(tmp_path, monkeypatch, pricing_names):
    monkeypatch.setattr(evaluator, "REPORTS", tmp_path)
    cases = [
        (pricing_names[0], "passed"),
        (pricing_names[1], "error"),
        (pricing_names[2], "skipped"),
        (pricing_names[3], "passed"),
    ]
    mock_pytest(monkeypatch, cases)

    result = evaluator.run_evaluation("pricing_case")
    assert result["passed"] == 2
    assert result["failed"] == 2
    assert result["errors"] == 1
    assert result["skipped"] == 1


def test_unexpected_test_is_rejected(tmp_path, monkeypatch, pricing_names):
    monkeypatch.setattr(evaluator, "REPORTS", tmp_path)
    cases = [(n, "passed") for n in pricing_names]
    cases.append(("test_unregistered", "passed"))
    mock_pytest(monkeypatch, cases)

    with pytest.raises(RuntimeError, match="extra="):
        evaluator.run_evaluation("pricing_case")


def test_missing_test_is_rejected(tmp_path, monkeypatch, pricing_names):
    monkeypatch.setattr(evaluator, "REPORTS", tmp_path)
    mock_pytest(monkeypatch, [(n, "passed") for n in pricing_names[:-1]])

    with pytest.raises(RuntimeError, match="missing="):
        evaluator.run_evaluation("pricing_case")


def test_duplicate_test_is_rejected(tmp_path, monkeypatch, pricing_names):
    monkeypatch.setattr(evaluator, "REPORTS", tmp_path)
    cases = [(n, "passed") for n in pricing_names]
    cases.append((pricing_names[0], "passed"))
    mock_pytest(monkeypatch, cases)

    with pytest.raises(RuntimeError, match="Duplicate collected"):
        evaluator.run_evaluation("pricing_case")
