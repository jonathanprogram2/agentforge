
import argparse
import json
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

EXPECTED_TESTS = {
    "inventory_case": {
        "test_interleaved_updates",
        "test_clamp_then_restock",
        "test_multiple_sku_movements",
        "test_no_movements",
    }
}


def evaluate_heldout(benchmark_name):
    report = ROOT / "reports" / "heldout.xml"

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            f"heldout/{benchmark_name}",
            "-q",
            "-p", "no:cacheprovider",
            f"--junitxml={report}",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=30,
    )

    if completed.returncode not in (0, 1) or not report.exists():
        raise RuntimeError(
            "Held-out test execution failed:\n"
            + completed.stdout[-2000:]
            + completed.stderr[-2000:]
        )

    tree = ET.parse(report)
    tests = {}

    for case in tree.findall(".//testcase"):
        name = case.get("name")

        if case.find("failure") is not None:
            status = "failed"
        elif case.find("error") is not None:
            status = "error"
        elif case.find("skipped") is not None:
            status = "skipped"
        else:
            status = "passed"

        tests[name] = status

    expected = EXPECTED_TESTS[benchmark_name]

    if set(tests) != expected:
        raise RuntimeError(
            f"Unexpected test collection: {sorted(tests)}"
        )

    passed = sum(status == "passed" for status in tests.values())

    return {
        "benchmark": benchmark_name,
        "total": len(expected),
        "passed": passed,
        "failed": len(expected) - passed,
        "success": passed == len(expected),
        "test_results": tests,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--benchmark",
        choices=EXPECTED_TESTS.keys(),
        required=True,
    )

    args = parser.parse_args()
    print(json.dumps(evaluate_heldout(args.benchmark)))
