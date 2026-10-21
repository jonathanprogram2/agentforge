

import json
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"

FAIL_TO_PASS = [
    "test_ten_percent_discount",
    "test_fifty_percent_discount",
]

PASS_TO_PASS = [
    "test_zero_discount",
    "test_zero_price",
]

def run_evaluation():
    REPORTS.mkdir(exist_ok=True)

    xml_path = REPORTS / "pricing_case.xml"

    if xml_path.exists():
        xml_path.unlink()

    command = [
        sys.executable,
        "-m",
        "pytest",
        "benchmarks/pricing_case",
        "-q",
        f"--junitxml={xml_path}",
    ]

    result = subprocess.run(
        command,
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=30,
    )

    if result.returncode not in (0, 1) or not xml_path.exists():
        raise RuntimeError(
            f"Benchmark execution error:\n{result.stdout}\n{result.stderr}"
        )
    
    tree = ET.parse(xml_path)
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

    expected = FAIL_TO_PASS + PASS_TO_PASS
    missing = set(expected) - set(tests)

    if missing:
        raise RuntimeError(f"Missing tests: {sorted(missing)}")
    
    summary = {
        "benchmark": "pricing_case",
        "total": len(tests),
        "passed": sum(s == "passed" for s in tests.values()),
        "failed": sum(s == "failed" for s in tests.values()),
        "fail_to_pass": {
            "passed": sum(tests[t] == "passed" for t in FAIL_TO_PASS),
            "total": len(FAIL_TO_PASS),
        },
        "pass_to_pass": {
            "passed": sum(tests[t] == "passed" for t in PASS_TO_PASS),
            "total": len(PASS_TO_PASS),
        },
        "test_results": tests,
    }

    output_path = REPORTS / "pricing_case_latest.json"
    output_path.write_text(
        json.dumps(summary, indent=2),
        encoding="utf-8",
    )

    print(json.dumps(summary, indent=2))
    return summary

if __name__ == "__main__":
    run_evaluation()
    


